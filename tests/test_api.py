"""Public HTTP API (api.py): REST /v1/<tool> and MCP /mcp, read-only."""
import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from sony_alpha_viet import api, server

POST_MD = (Path(__file__).parent / "fixtures/colorlab-post.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def client():
    server.make_public()
    with TestClient(api.build_app(), base_url="https://api.alphacolorlab.com") as c:
        yield c


def test_index_lists_only_read_tools(client):
    r = client.get("/v1")
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == "*"
    tools = r.json()["tools"]
    assert "lookup_term" in tools and "colorlab_article" in tools
    assert not set(tools) & set(server.WRITE_TOOLS)


def test_get_with_typed_query(client):
    r = client.get("/v1/slugify", params={"text": "Chế độ ưu tiên khẩu độ", "max_words": "3"})
    assert r.status_code == 200, r.text
    assert r.json() == "che-do-uu"


def test_post_json_body(client):
    r = client.post("/v1/colorlab_article", json={"source": POST_MD})
    assert r.status_code == 200, r.text
    assert r.json()["article"]["id"] == "lay-net-bang-ngon-tay-cai" and r.json()["problems"] == []


def test_public_mode_never_reads_or_writes_files(client):
    r = client.post("/v1/colorlab_article", json={"source": "/etc/hostname"})
    assert r.json()["article"]["title"] == ""          # treated as text, not opened
    r = client.post("/v1/colorlab_html", json={"source": POST_MD, "out": "/tmp/should-not-exist.html"})
    assert "html" in r.json() and not Path("/tmp/should-not-exist.html").exists()


def test_errors(client):
    assert client.get("/v1/record_term").status_code == 404     # write tool removed
    assert client.get("/v1/nope").status_code == 404
    assert client.post("/v1/slugify", content="[1]", headers={"content-type": "application/json"}).status_code == 400
    assert client.options("/v1/slugify").status_code == 204


def test_mcp_endpoint(client):
    headers = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}
    assert client.post("/mcp", json=init, headers=headers).status_code == 200
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, headers=headers)
    names = {t["name"] for t in json.loads(r.text)["result"]["tools"]}
    assert "search_knowledge" in names and "commit_memory" not in names
