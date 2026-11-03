"""Build portable/knowledge/ from the skill so Custom GPTs, Gemini Gems and other chat apps get the same rules.

Run after editing skills/sony-alpha-viet: uv run python scripts/build_portable.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "sony-alpha-viet"
OUT = ROOT / "portable" / "knowledge"
FILES = ["references/glossary-vi.md", "references/sony-menu-terms.md", "references/seo-aio-checklist.md",
         "references/sony-core-principles.md", "references/writing-style-vi.md",
         "templates/blog-post-template.md", "templates/faq-schema.json",
         "examples/example-blog-post.md"]
# Tool calls only exist with the MCP server; chat apps get a plain-language note instead.
MCP_NOTE = "> Ghi chú: các lệnh `mcp__…`/tên công cụ trong file này chỉ có khi dùng MCP server sony-alpha-viet. " \
           "Không có công cụ thì làm thủ công theo cùng quy tắc và ghi \"chưa kiểm bằng MCP\".\n\n"
PROMPT_LIMIT = 8000  # Custom GPT instructions limit
META_LIMIT = 2000  # Meta AI Studio instructions limit


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for rel in FILES:
        text = (SKILL / rel).read_text(encoding="utf-8")
        if rel.endswith(".md") and re.search(r"mcp__|prepare_batch|check_translation", text):
            text = MCP_NOTE + text
        (OUT / Path(rel).name).write_text(text, encoding="utf-8")
    n = len((ROOT / "portable" / "system-prompt.md").read_text(encoding="utf-8"))
    print(f"{len(FILES)} file → {OUT.relative_to(ROOT)}; system-prompt.md {n} ký tự" + (" (VƯỢT 8.000 của Custom GPT!)" if n > PROMPT_LIMIT else ""))
    m = len((ROOT / "portable" / "meta-ai-studio" / "instructions.md").read_text(encoding="utf-8").strip())
    print(f"meta-ai-studio/instructions.md {m} ký tự" + (" (VƯỢT 2.000 của Meta AI Studio!)" if m > META_LIMIT else ""))


if __name__ == "__main__":
    main()
