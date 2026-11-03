"""HTTP API for alphaskill: MCP (Streamable HTTP) at /mcp and REST JSON at /v1/<tool>.

GET  /v1                    -> version, data counts, every tool with its JSON-schema params
GET  /v1/<tool>?arg=value   -> call a tool with query parameters
POST /v1/<tool>  {"arg": …} -> call a tool with a JSON body

Local:   uv run sony-alpha-viet-mcp --http --read-only        Vercel: `app.py` at the repo root.
"""
from __future__ import annotations

import json

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from . import server

CORS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "content-type, mcp-protocol-version, mcp-session-id"}


def _version() -> str:
    try:
        from importlib.metadata import version
        return version("sony-alpha-viet")
    except Exception:
        return "dev"


def _coerce(value: str, spec: dict):
    """Query strings are text; turn them into the type the tool's schema declares."""
    kind = spec.get("type") or next((x.get("type") for x in spec.get("anyOf", []) if x.get("type") != "null"), "string")
    if kind == "integer":
        return int(value)
    if kind == "number":
        return float(value)
    if kind == "boolean":
        return value.lower() in ("1", "true", "yes", "on")
    if kind in ("array", "object"):
        return json.loads(value)
    return value


def _json(data, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status, headers=CORS)


async def index(request: Request) -> JSONResponse:
    tools = server.mcp._tool_manager._tools
    return _json({"name": "sony-alpha-viet", "version": _version(), "mcp": "/mcp", "rest": "/v1/<tool>",
                  "data": server.data_info(),
                  "tools": {n: {"description": (t.description or "").strip().split("\n")[0],
                                "params": t.parameters.get("properties", {}),
                                "required": t.parameters.get("required", [])} for n, t in sorted(tools.items())}})


async def call(request: Request) -> Response:
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=CORS)
    name = request.path_params["tool"]
    tool = server.mcp._tool_manager._tools.get(name)
    if tool is None:
        return _json({"error": f"không có tool '{name}'", "tools": "/v1"}, 404)
    props = tool.parameters.get("properties", {})
    try:
        if request.method == "GET":
            args = {k: _coerce(v, props.get(k, {})) for k, v in request.query_params.items()}
        else:
            args = await request.json()
            if not isinstance(args, dict):
                raise ValueError("body phải là một JSON object")
        return _json(await tool.run(args))
    except Exception as e:  # bad arguments or a tool error: the caller can fix and retry
        return _json({"error": str(e)[:500]}, 400)


def build_app():
    """The ASGI app (MCP + REST). `server.mcp` is a module singleton, so build once per process."""
    import os
    from mcp.server.transport_security import TransportSecuritySettings
    mcp = server.mcp
    mcp.settings.stateless_http = True   # serverless: no session affinity between requests
    mcp.settings.json_response = True
    # /mcp keeps DNS-rebinding protection: only these Host headers (Vercel sets VERCEL_URL per deployment).
    hosts = ["127.0.0.1:*", "localhost:*", "api.alphacolorlab.com",
             *(os.environ.get(k) for k in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL") if os.environ.get(k)),
             *filter(None, os.environ.get("SONY_VN_HOSTS", "").split(","))]
    mcp.settings.transport_security = TransportSecuritySettings(
        allowed_hosts=hosts, allowed_origins=["https://alphacolorlab.com", "https://www.alphacolorlab.com",
                                              "http://localhost:*", "http://127.0.0.1:*"])
    mcp.custom_route("/v1", methods=["GET"])(index)
    mcp.custom_route("/v1/{tool}", methods=["GET", "POST", "OPTIONS"])(call)
    mcp.custom_route("/", methods=["GET"])(lambda request: RedirectResponse("/v1"))
    return mcp.streamable_http_app()
