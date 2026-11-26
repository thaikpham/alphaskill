"""One command for every tool in this repo: `alphaskill <command> [args]`. Run `alphaskill` alone for the list.

Each command calls the existing entry point unchanged (server, Llama agent, Obsidian sync, review sheet, scripts/),
so `sony-alpha-viet-mcp`, `python -m sony_alpha_viet.xls.review_pairs` and `scripts/*.py` keep working.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo clone: <root>/src/sony_alpha_viet/cli.py


def _call(prog: str, fn, args: list[str]) -> int:
    """Run an argparse main() as if it had been started as `prog args...`."""
    saved = sys.argv
    sys.argv = [prog, *args]
    try:
        return fn() or 0
    finally:
        sys.argv = saved


def _repo(cmd: str) -> Path:
    if not (ROOT / "scripts").is_dir():
        sys.exit(f"alphaskill {cmd}: cần bản clone của github.com/thaikpham/alphaskill (không thấy thư mục scripts/)")
    return ROOT


def _script(cmd: str, name: str, args: list[str], env: dict | None = None) -> int:
    root = _repo(cmd)
    runner = ["bash"] if name.endswith(".sh") else [sys.executable]
    return subprocess.call([*runner, str(root / "scripts" / name), *args], cwd=root, env=env)


def _private_data() -> Path | None:
    """Data folder set by $SONY_VN_DATA or config.json; None when only the sample copy is in use."""
    from . import paths
    return paths.DATA if paths.DATA_SOURCE.startswith(("env ", "config ")) else None


def serve(args):
    from . import server
    return _call("alphaskill serve", server.main, args)


def info(args):
    if args:
        print("dùng: alphaskill info", file=sys.stderr)
        return 2
    from . import server
    print(json.dumps(server.data_info(), ensure_ascii=False, indent=1))
    return 0


def agent(args):
    from . import llama_agent
    return _call("alphaskill agent", llama_agent.main, args)


def review_pairs(args):
    from .xls import review_pairs as rp
    return rp.main(args)


def obsidian(args):
    from . import obsidian as ob
    return _call("alphaskill obsidian", ob.main, args)


def build(args):
    return _script("build", "build_portable.py", args)


def export(args):
    if len(args) > 2 or any(a.startswith("-") for a in args):
        print("dùng: alphaskill export [SRC] [OUT]   (mặc định: thư mục dữ liệu riêng → data-sample/)", file=sys.stderr)
        return 2
    src = args[0] if args else _private_data()
    if src is None:
        print("alphaskill export: chưa có dữ liệu riêng. Đặt SONY_VN_DATA, thêm \"data\" vào config.json, hoặc truyền SRC.",
              file=sys.stderr)
        return 2
    out = args[1] if len(args) > 1 else _repo("export") / "data-sample"
    return _script("export", "export_public_data.py", [str(src), str(out)])


def publish(args):
    env = dict(os.environ)
    if not env.get("SONY_VN_DATA"):
        data = _private_data()
        if data is None:
            print("alphaskill publish: chưa có dữ liệu riêng. Đặt SONY_VN_DATA hoặc thêm \"data\" vào config.json.",
                  file=sys.stderr)
            return 2
        env["SONY_VN_DATA"] = str(data)
    return _script("publish", "publish.sh", args, env)


def check(args):
    """What CI runs, in order; stops at the first failure."""
    root = _repo("check")
    steps = [
        ("ruff", [sys.executable, "-m", "ruff", "check", "--select", "F", "src/", "tests/", "scripts/"]),
        ("pytest", [sys.executable, "-m", "pytest", "-q", *args]),
        ("build --check", [sys.executable, "scripts/build_portable.py", "--check"]),
    ]
    for name, cmd in steps:
        print(f"▶ {name}", flush=True)
        code = subprocess.call(cmd, cwd=root)
        if code:
            print(f"✗ {name} lỗi (mã {code})", file=sys.stderr)
            return code
    print("✓ tất cả đều qua")
    return 0


# name: (handler, arguments, help) — the order here is the order of `alphaskill --help`
COMMANDS = {
    "serve": (serve, "[--http] [--read-only] [--host H] [--port P]",
              "MCP server: stdio cho Claude Code / Gemini CLI; --http mở MCP ở /mcp và REST ở /v1/<tool>"),
    "info": (info, "", "thư mục dữ liệu đang dùng và số lượng thuật ngữ, quy tắc, bộ nhớ dịch, ghi chú"),
    "agent": (agent, "[\"yêu cầu\"] [--model M] [--base-url URL] [--allow-write]",
              "agent Llama chạy trên máy (Ollama hoặc Llama API) dùng các tool MCP"),
    "review-pairs": (review_pairs, "FOLDER OUT.xlsx MAPPING.json",
                     "gom bộ *_VN.xls thành file rà soát English | Vietnamese không trùng + mapping"),
    "obsidian": (obsidian, "export | import [--apply] | audit NOTE [--keyword K]", "đồng bộ với vault Obsidian"),
    "build": (build, "[--check]", "sinh lại llms-*.txt và portable/ từ skill + data-sample (cần bản clone)"),
    "export": (export, "[SRC] [OUT]", "lọc dữ liệu riêng thành data-sample/ công khai (cần bản clone)"),
    "publish": (publish, "[--no-push]", "Obsidian → dữ liệu riêng → data-sample/ → api.alphacolorlab.com (cần bản clone)"),
    "check": (check, "[pytest args]", "chạy đúng như CI: ruff, pytest, build --check (cần bản clone)"),
}


def usage() -> str:
    lines = ["alphaskill: Sony Alpha Việt (dịch menu, tài liệu, blog SEO/AIO, đào tạo)", "", "Dùng: alphaskill <lệnh> [tham số]", ""]
    for n, (_, a, h) in COMMANDS.items():
        lines += [f"  {n} {a}".rstrip(), f"      {h}"]
    lines += ["", "alphaskill <lệnh> --help để xem chi tiết từng lệnh (serve, agent, obsidian, build)."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(usage())
        return 0
    if argv[0] in ("-V", "--version"):
        from importlib.metadata import version
        print(f"alphaskill {version('sony-alpha-viet')}")
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        print(f"alphaskill: không có lệnh '{cmd}'\n\n{usage()}", file=sys.stderr)
        return 2
    return COMMANDS[cmd][0](rest) or 0


if __name__ == "__main__":
    sys.exit(main())
