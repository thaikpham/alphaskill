"""Llama agent loop against the real MCP server (spawned read-only) with a scripted fake model."""
import asyncio


def test_agent_calls_mcp_tool_and_answers(env):
    from sony_alpha_viet import llama_agent
    seen = []

    async def fake_chat(http, base_url, model, messages, tools):
        seen.append(messages[-1])
        names = {t["function"]["name"] for t in tools}
        assert "check_translation" in names and "record_term" not in names  # read-only tool set
        if messages[-1]["role"] == "user":
            return {"content": "", "tool_calls": [{"id": "c1", "type": "function", "function": {
                "name": "check_translation", "arguments": '{"en": "Range of Zoom Assist", "vi": "Dải hỗ trợ thu phóng"}'}}]}
        return {"content": "Range of Zoom Assist = Dải hỗ trợ Zoom"}

    out = asyncio.run(llama_agent.run("Dịch: Range of Zoom Assist", "http://x", "fake", chat_fn=fake_chat))
    assert out == "Range of Zoom Assist = Dải hỗ trợ Zoom"
    assert seen[-1]["role"] == "tool" and "Dải hỗ trợ Zoom" in seen[-1]["content"]


def test_agent_reports_bad_tool_arguments(env):
    from sony_alpha_viet import llama_agent

    async def fake_chat(http, base_url, model, messages, tools):
        if messages[-1]["role"] == "user":
            return {"content": "", "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "slugify", "arguments": "{not json"}}]}
        assert "error" in messages[-1]["content"]
        return {"content": "ok"}

    assert asyncio.run(llama_agent.run("x", "http://x", "fake", chat_fn=fake_chat)) == "ok"


def test_text_tool_call_fallback():
    from sony_alpha_viet.llama_agent import _drop_nulls, text_tool_calls
    c = text_tool_calls('{"name":"prepare_batch","parameters":{"items":[{"id":"None","en":"Focus Area","max_width":null}]}}', {"prepare_batch"})
    assert c and c[0]["function"]["name"] == "prepare_batch"
    import json
    assert _drop_nulls(json.loads(c[0]["function"]["arguments"])) == {"items": [{"en": "Focus Area"}]}
    assert text_tool_calls("Khẩu độ là Aperture.", {"prepare_batch"}) == []


def test_text_tool_call_repairs_stray_bracket():
    from sony_alpha_viet.llama_agent import text_tool_calls
    bad = '{"name":"prepare_batch","parameters":{"items":[{"en":"Focus Area"},{"en":"Silent Shooting"}]}]}'
    c = text_tool_calls(bad, {"prepare_batch"})
    assert c and '"Silent Shooting"' in c[0]["function"]["arguments"]
