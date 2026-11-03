"""Llama agent: Meta Llama models (Ollama locally, or Meta's Llama API) using the sony-alpha-viet MCP tools.

Any OpenAI-compatible /chat/completions endpoint with tool calling works:
  Ollama (default)  --base-url http://localhost:11434/v1        --model llama3.2:3b
  Meta Llama API    --base-url https://api.llama.com/compat/v1  --model Llama-4-Maverick-17B-128E-Instruct-FP8  (LLAMA_API_KEY)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
# Small local models handle a short tool list far better than all 25 tools.
DEFAULT_TOOLS = ["get_guidelines", "prepare_batch", "lookup_term", "search_memory", "check_translation", "suggest_short",
                 "lookup_prose_term", "slugify", "count_words", "style_lint", "seo_audit", "faq_schema"]
TOOL_NOTE = """

## Công cụ
Bạn có công cụ MCP sony-alpha-viet. Dịch menu: gọi prepare_batch trước. Có exact_match thì dùng nguyên văn. Không có exact_match thì TỰ DỊCH theo nghĩa chuỗi tiếng Anh; các bản trong "memory" chỉ là chuỗi khác gần giống, KHÔNG chép (ví dụ "NR Shooting = Chụp giảm nhiễu" không phải bản dịch của "Silent Shooting"). Sau đó gọi check_translation cho từng chuỗi tự dịch và dùng trường "text" nó trả về. Xuất bảng EN | VI | Ghi chú. Blog: sau khi viết, gọi seo_audit và faq_schema thay vì tự đếm. Chỉ gọi công cụ khi cần; trả lời cuối cùng bằng tiếng Việt. Chỉ ghi "đã kiểm tra" cho chuỗi thật sự đã qua check_translation; chuỗi lấy từ exact_match ghi "bộ nhớ đã duyệt"; không bịa layout (max_width, font) nếu người dùng không cho."""


def system_prompt() -> str:
    p = ROOT / "portable" / "system-prompt.md"
    return (p.read_text(encoding="utf-8") if p.exists() else "Bạn là biên tập viên tiếng Việt về máy ảnh Sony Alpha.") + TOOL_NOTE


def _drop_nulls(v):
    if isinstance(v, str) and v[:1] in "[{":  # models sometimes send a list/object as a JSON string
        try:
            return _drop_nulls(json.loads(v))
        except json.JSONDecodeError:
            return v
    if isinstance(v, dict):
        return {k: _drop_nulls(x) for k, x in v.items() if x is not None and x != "None"}
    if isinstance(v, list):
        return [_drop_nulls(x) for x in v]
    return v


def _balance(s: str) -> str:
    """Drop closing brackets that don't match (e.g. a stray ']' small models emit) and close what's left open."""
    out, stack, in_str, esc = [], [], False, False
    for ch in s:
        if in_str:
            out.append(ch)
            esc = ch == "\\" and not esc
            if ch == '"' and not esc:
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if not stack or stack[-1] != ch:
                continue
            stack.pop()
            out.append(ch)
            if not stack:
                break
            continue
        out.append(ch)
    return "".join(out) + "".join(reversed(stack))


def text_tool_calls(content: str, names: set[str]) -> list[dict]:
    """Small Llama models often print {"name": …, "parameters": …} as text instead of a structured tool call."""
    s = (content or "").strip().strip("`")
    s = s[s.find("{"):] if "{" in s else ""
    calls, dec, i = [], json.JSONDecoder(), 0
    while s and i < len(s):
        try:
            obj, end = dec.raw_decode(s, i)
        except json.JSONDecodeError:
            fixed = _balance(s[i:])
            try:
                obj, end = json.loads(fixed), i + len(fixed)
            except json.JSONDecodeError:
                break
        if isinstance(obj, dict) and obj.get("name") in names:
            args = obj.get("parameters", obj.get("arguments", {}))
            calls.append({"id": f"t{len(calls)}", "type": "function",
                          "function": {"name": obj["name"], "arguments": json.dumps(args, ensure_ascii=False)}})
        nxt = s.find("{", end)
        if nxt < 0:
            break
        i = nxt
    return calls


def footer(used: list[str], data: dict | None = None) -> str:
    """Ground truth on what was actually checked; models tend to claim verification they didn't do."""
    names = list(dict.fromkeys(used))
    line = "\n\n---\nCông cụ đã chạy: " + (", ".join(names) if names else "không có")
    if data and data.get("is_sample_data"):
        line += f". ⚠ Đang dùng DỮ LIỆU MẪU ({data.get('data_path')}), không có bộ nhớ dịch — đặt SONY_VN_DATA hoặc ~/.config/sony-alpha-viet/config.json"
    if "check_translation" not in names:
        line += ". Bản dịch CHƯA qua check_translation — hãy duyệt lại."
    return line


def to_openai_tool(t) -> dict:
    return {"type": "function", "function": {"name": t.name, "description": (t.description or "")[:1000],
                                             "parameters": t.inputSchema or {"type": "object", "properties": {}}}}


async def chat(client: httpx.AsyncClient, base_url: str, model: str, messages: list, tools: list) -> dict:
    r = await client.post(f"{base_url.rstrip('/')}/chat/completions",
                          json={"model": model, "messages": messages, "tools": tools, "temperature": 0.2})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


async def run(prompt: str, base_url: str, model: str, api_key: str = "", tools: list[str] | None = None,
              allow_write: bool = False, max_steps: int = 8, verbose: bool = False, chat_fn=chat) -> str:
    """One request → final answer. The MCP server is spawned read-only unless allow_write."""
    args = ["-m", "sony_alpha_viet.server"] + ([] if allow_write else ["--read-only"])
    params = StdioServerParameters(command=sys.executable, args=args, env=dict(os.environ), cwd=str(ROOT))
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session, \
            httpx.AsyncClient(headers=headers, timeout=300) as http:
        await session.initialize()
        try:
            data = json.loads((await session.call_tool("data_info", {})).content[0].text)
        except Exception:
            data = None
        available = (await session.list_tools()).tools
        wanted = set(tools or DEFAULT_TOOLS)
        oa_tools = [to_openai_tool(t) for t in available if t.name in wanted]
        messages = [{"role": "system", "content": system_prompt()}, {"role": "user", "content": prompt}]
        used: list[str] = []
        for _ in range(max_steps):
            msg = await chat_fn(http, base_url, model, messages, oa_tools)
            calls = msg.get("tool_calls") or text_tool_calls(msg.get("content") or "", {t["function"]["name"] for t in oa_tools})
            messages.append({"role": "assistant", "content": "" if calls else msg.get("content") or "", **({"tool_calls": calls} if calls else {})})
            if not calls:
                return (msg.get("content") or "") + footer(used, data)
            for c in calls:
                name = c["function"]["name"]
                raw = c["function"].get("arguments") or "{}"
                try:
                    a = _drop_nulls(json.loads(raw) if isinstance(raw, str) else raw)
                    res = await session.call_tool(name, a)
                    out = "\n".join(getattr(x, "text", "") for x in res.content)
                    used.append(name)
                except Exception as e:  # bad arguments from the model: report back so it can retry
                    out = json.dumps({"error": str(e)}, ensure_ascii=False)
                if verbose:
                    print(f"[tool] {name}({raw}) → {out[:300]}", file=sys.stderr)
                messages.append({"role": "tool", "tool_call_id": c.get("id", name), "name": name, "content": out[:12000]})
        return "(Dừng: quá số bước gọi công cụ cho phép.)" + footer(used, data)


def main():
    ap = argparse.ArgumentParser(prog="sony-alpha-viet-llama", description="Agent Llama dùng công cụ MCP sony-alpha-viet")
    ap.add_argument("prompt", nargs="?", help="yêu cầu; bỏ trống để vào chế độ hội thoại")
    ap.add_argument("--base-url", default=os.environ.get("LLAMA_BASE_URL", "http://localhost:11434/v1"))
    ap.add_argument("--model", default=os.environ.get("LLAMA_MODEL", "llama3.2:3b"))
    ap.add_argument("--tools", help="danh sách tool, cách nhau dấu phẩy (mặc định: bộ đọc/kiểm tra)")
    ap.add_argument("--allow-write", action="store_true", help="cho phép tool ghi bộ nhớ dịch")
    ap.add_argument("-v", "--verbose", action="store_true", help="in các lần gọi tool")
    a = ap.parse_args()
    key = os.environ.get("LLAMA_API_KEY", "")
    tools = a.tools.split(",") if a.tools else None
    go = lambda p: asyncio.run(run(p, a.base_url, a.model, key, tools, a.allow_write, verbose=a.verbose))
    if a.prompt:
        print(go(a.prompt))
        return
    print(f"Sony Alpha Việt × {a.model} — gõ yêu cầu, Ctrl+D để thoát.")
    for line in sys.stdin:
        if line.strip():
            print(go(line.strip()), "\n")


if __name__ == "__main__":
    main()
