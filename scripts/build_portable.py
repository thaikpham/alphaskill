"""Build the chat-app bundle: portable/knowledge/, llms-full.txt, llms-blog.txt, llms-knowledge.txt and llms.txt.

llms-full.txt is the core (role, menu rules, glossary, examples). llms-blog.txt and llms-knowledge.txt are add-ons
that the core points to. Custom GPTs, Gems, Meta AI and any AI given a raw link read these generated files, so they
follow the same rules as the Claude Code skill. Run after editing skills/sony-alpha-viet, data-sample/ or
portable/system-prompt.md:
    uv run python scripts/build_portable.py
Verify the committed outputs without writing anything (exit 1 when stale):
    uv run python scripts/build_portable.py --check
"""
from __future__ import annotations

import argparse
import functools
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # the rule engine is the MCP server's own code: import it, don't copy it
from sony_alpha_viet import core  # noqa: E402
SKILL = ROOT / "skills" / "sony-alpha-viet"
DATA = ROOT / "data-sample"
OUT = ROOT / "portable" / "knowledge"
FULL = ROOT / "llms-full.txt"
BLOG = ROOT / "llms-blog.txt"
KNOWLEDGE = ROOT / "llms-knowledge.txt"
INDEX = ROOT / "llms.txt"
RAW = "https://raw.githubusercontent.com/thaikpham/alphaskill/main/"
API = "https://api.alphacolorlab.com"
FILES = ["references/glossary-vi.md", "references/sony-menu-terms.md", "references/seo-aio-checklist.md",
         "references/sony-core-principles.md", "references/writing-style-vi.md", "references/trainer-vi.md",
         "references/colorlab-vi.md",
         "templates/blog-post-template.md", "templates/faq-schema.json",
         "examples/example-blog-post.md", "examples/example-menu-translation.md"]
FILE_ROLE = {  # the three root bundles, in the order a reader should open them
    "llms-full.txt": "lõi: vai trò, quy tắc dịch menu và tài liệu, bảng thuật ngữ, ví dụ dịch. Đọc trước",
    "llms-blog.txt": "thêm cho viết blog SEO/AIO: bảo vệ Sony, checklist, khung bài, FAQ schema",
    "llms-knowledge.txt": "thêm cho đào tạo và giáo án: vai trò trainer, kiến thức nền",
}
# Tool calls only exist with the MCP server; chat apps get a plain-language note instead.
MCP_NOTE = "> Ghi chú: các lệnh `mcp__…`/tên công cụ trong file này chỉ có khi dùng MCP server sony-alpha-viet. " \
           "Không có công cụ thì làm thủ công theo cùng quy tắc và ghi \"chưa kiểm bằng MCP\".\n\n"
MCP_RE = re.compile(r"mcp__|prepare_batch|check_translation")
PROMPT_LIMIT = 8000  # Custom GPT instructions limit
META_LIMIT = 2000  # Meta AI Studio instructions limit
CORE_LIMIT = 90 * 1024  # target for llms-full.txt; the test allows 95 KB
KNOWLEDGE_FULL_LIMIT = 250 * 1024  # llms-knowledge.txt inlines every note below this total, else only links them
HEADING = re.compile(r"^(#{1,6})(\s.*)?$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RULE_REF = re.compile(r"quy tắc mục (\d+)")  # exceptions.json cites rules.md sections by number
GLOSSARY_LEAD = "Tra ở đây trước. Không có → dịch, đánh dấu [thuật ngữ mới]."
GLOSSARY_NOTE = "Cột Ngắn trống khi bằng VI. (khóa) trong Ghi chú = thuật ngữ đã chốt, không tự đổi."
DESCRIPTIONS = {  # files whose H1 is a placeholder or missing
    "blog-post-template.md": "Khung bài blog AIO-first: TL;DR, H2, bảng so sánh, FAQ, Key Takeaways",
    "faq-schema.json": "Mẫu JSON-LD Article + FAQPage cho bài blog",
}
EXCEPTION_LABELS = {"sony_names": "Tên Sony", "apps": "Ứng dụng", "standards": "Chuẩn", "loanwords": "Từ mượn",
                    "abbreviations": "Viết tắt", "rule": "Quy tắc", "languages": "Ngôn ngữ"}


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def load(rel: str):
    return json.loads(read(rel))


def skill_text(rel: str) -> str:
    """Skill file, with the MCP note added when it mentions tool calls."""
    text = (SKILL / rel).read_text(encoding="utf-8")
    if rel.endswith(".md") and MCP_RE.search(text):
        text = MCP_NOTE + text
    return text


def h1_of(text: str) -> str | None:
    for line in text.split("\n"):
        m = HEADING.match(line)
        if m and len(m.group(1)) == 1:
            return line[1:].strip()
    return None


def describe(name: str, text: str) -> str:
    """Label for a file: explicit text where the H1 is a placeholder or missing, else the H1."""
    return DESCRIPTIONS.get(name) or h1_of(text) or Path(name).stem


def demote(text: str, base: int) -> str:
    """Shift headings under a wrapper heading at level `base`: H2 -> base+1, H3 -> base+2, ...
    The first H1 is dropped (the wrapper replaces it). Lines inside fenced code are left alone."""
    out, fence, dropped = [], "", False
    for line in text.split("\n"):
        stripped = line.strip()
        if fence:
            if stripped and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                fence = ""
        elif FENCE.match(line):
            fence = FENCE.match(line).group(1)
        else:
            m = HEADING.match(line)
            if m:
                level = len(m.group(1))
                if level == 1 and not dropped:
                    dropped = True
                    continue
                line = "#" * min(6, base + level - 1) + line[level:]
        out.append(line)
    return "\n".join(out).strip("\n") + "\n"


def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].split("\n"):
        key, sep, value = line.partition(":")
        if sep and key and not key.startswith(" "):
            meta[key.strip()] = value.strip().strip("\"'")
    return meta, text[end + 5:]


def cell(value) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def code(value) -> str:
    return f"`{cell(value)}`" if value else "(rỗng)"


def slug(heading: str) -> str:
    """GitHub-style anchor for a heading."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def project_version() -> str:
    m = re.search(r'^version = "([^"]+)"', read("pyproject.toml"), re.M)
    if not m:
        raise SystemExit("không tìm thấy version trong pyproject.toml")
    return m.group(1)


def glossary_md(entries: list[dict], cat_level: int) -> str:
    groups: dict[str, list[dict]] = {}
    for e in entries:
        groups.setdefault(e.get("category") or "chung", []).append(e)
    lines = []
    for cat in sorted(groups):
        rows = []
        for e in groups[cat]:
            short = "" if e.get("short") in (None, "", e.get("vi")) else e["short"]
            note = "; ".join(p for p in ["(khóa)" if e.get("locked") else "", e.get("note") or ""] if p)
            rows.append(f"| {cell(e.get('en'))} | {cell(e.get('vi'))} | {cell(short)} | {cell(note)} |")
        lines += [f"{'#' * cat_level} {cat} ({len(rows)})", "", "| EN | VI | Ngắn | Ghi chú |", "|---|---|---|---|",
                  *rows, ""]
    return "\n".join(lines).strip("\n") + "\n"


@functools.lru_cache(maxsize=None)
def rules_store() -> core.Store:
    """The rule engine's store, read from data-sample/ only: never $SONY_VN_DATA or the user's config,
    so the output is the same on every machine."""
    saved, core.DATA = core.DATA, DATA
    try:
        return core.Store()
    finally:
        core.DATA = saved


def rewrite_value(store: core.Store, value: str, en: str) -> tuple[str, list[str]]:
    """value after the check_translation rules (no width fit), keeping the glossary's casing.
    Returns (value, []) when nothing changes."""
    res = core.apply_rules(store, value, en)
    out = res["text"]
    if not res["changed"] or (out[1:] == value[1:] and out[:1].lower() == value[:1].lower()):
        return value, []  # only the first letter's case moved: keep the glossary's
    if value[:1].islower():  # a rewrite keeps the glossary's lowercase start; an uppercase start is a proper noun or acronym
        out = out[:1].lower() + out[1:]
    if out == value:
        return value, []
    # no applied id means the keep_english step changed the text
    return out, [a["rule"] for a in res["applied"]] or ["keep_english"]


def rule_glossary(glossary: list[dict]) -> tuple[list[dict], list[str]]:
    """Entries as rendered: vi and short go through the rule engine; keep_english terms are skipped.
    A rewritten entry gets "(đã áp quy tắc rNNN)" at the end of its note. Returns (entries, en of rewritten entries)."""
    store = rules_store()
    keep = {" ".join(k["term"].lower().split()) for k in store.keep if k.get("term")}
    out, changed = [], []
    for e in glossary:
        if " ".join(e["en"].lower().split()) in keep:
            out.append(e)
            continue
        changes, ids = {}, []
        for field in ("vi", "short"):
            if e.get(field):
                new, used = rewrite_value(store, e[field], e["en"])
                if new != e[field]:
                    changes[field] = new
                    ids += [u for u in used if u not in ids]
        if not changes:
            out.append(e)
            continue
        note = " ".join(p for p in [e.get("note") or "", f"(đã áp quy tắc {', '.join(ids)})"] if p)
        out.append({**e, **changes, "note": note})
        changed.append(e["en"])
    return out, changed


def glossary_section(glossary: list[dict]) -> str:
    """The one lookup place: the hand-written core table first, then every term grouped by category."""
    return "\n\n".join([
        GLOSSARY_LEAD + "\n\n" + GLOSSARY_NOTE,
        "### Bảng cốt lõi có tiếng Nhật và dạng văn xuôi\n\n" + demote(skill_text("references/glossary-vi.md"), 3),
        "### Bảng đầy đủ theo danh mục\n\n" + glossary_md(glossary, 4),
    ])


def keep_english_md(items: list[dict]) -> str:
    lines = ["| Thuật ngữ | Bản Việt → viết thành | Lý do |", "|---|---|---|"]
    for it in items:
        variants = "; ".join(f"{cell(vi)} → {cell(tpl.replace('{term}', it['term']))}"
                             for vi, tpl in it.get("vi_variants", {}).items())
        lines.append(f"| {cell(it['term'])} | {variants} | {cell(it.get('why'))} |")
    return "\n".join(lines) + "\n"


def merge_split(items: list[str]) -> list[str]:
    """exceptions.json splits some multi-word names into separate items ("Bahasa", "Indonesia"); join them back."""
    merged: list[str] = []
    for item in items:
        if merged and merged[-1] == "Bahasa":
            merged[-1] = f"Bahasa {item}"
        else:
            merged.append(item)
    return merged


def rule_titles() -> dict[str, str]:
    """Numbered sections of data-sample/rules.md: '### 8. GIÁ TRỊ …' -> {'8': 'GIÁ TRỊ …'}."""
    text = (DATA / "rules.md").read_text(encoding="utf-8")
    return {n: title.strip() for n, title in re.findall(r"^### (\d+)\. (.+)$", text, re.M)}


def section_refs(text: str) -> str:
    """'quy tắc mục 8' points at rules.md section 8, which the bundle does not number: write that section's title instead."""
    titles = rule_titles()
    return RULE_REF.sub(lambda m: f'quy tắc "{titles[m.group(1)]}"' if m.group(1) in titles else m.group(0), text)


def exceptions_md(groups: dict) -> str:
    parts = []
    for name, value in groups.items():
        label = EXCEPTION_LABELS.get(name, name)
        if isinstance(value, str):
            parts.append(f"**{label}:** {section_refs(value.strip())}")
        else:
            items = merge_split(value)
            parts.append(f"**{label} ({len(items)}):** " + ", ".join(cell(i) for i in items))
    return "\n\n".join(parts) + "\n"


def rules_md(rules: dict) -> str:
    active = [r for r in rules["substitutions"] if not r.get("disabled")]
    banned = rules["banned"]
    lines = [f"**Thay thế đang bật ({len(active)}):**", "", "| Mẫu (regex) | Thay bằng |", "|---|---|",
             *[f"| {code(r['pattern'])} | {code(r['replace'])} |" for r in active], "",
             f"**Từ cấm ({len(banned)}):**", "", "| Mẫu cấm (regex) | Lý do |", "|---|---|",
             *[f"| {code(b['pattern'])} | {cell(b.get('why'))} |" for b in banned], ""]
    if rules.get("exact"):
        lines += ["**Khớp nguyên văn:**", "", *[f"- {code(k)} → {code(v)}" for k, v in rules["exact"].items()], ""]
    return "\n".join(lines)


def first_line(body: str) -> str:
    for line in body.split("\n"):
        s = line.strip()
        if s and not s.startswith(("#", "```", "|", "![")):
            return s[:160]
    return ""


def knowledge_notes() -> list[Path]:
    return sorted((DATA / "knowledge").rglob("*.md"), key=lambda p: p.relative_to(DATA).as_posix())


def knowledge_section(notes: list[Path]) -> str:
    total = sum(len(p.read_bytes()) for p in notes)
    if total <= KNOWLEDGE_FULL_LIMIT:
        parts = []
        for p in notes:
            meta, body = split_front_matter(p.read_text(encoding="utf-8"))
            title = meta.get("title") or h1_of(body) or p.stem
            parts.append(f"### {title}\n\n{demote(body, 3)}")
        return "\n".join(parts)
    lines = [f"Kiến thức đầy đủ dài {total // 1024} KB, vượt {KNOWLEDGE_FULL_LIMIT // 1024} KB nên đây là chỉ mục. "
             "Mở link khi cần:", ""]
    for p in notes:
        meta, body = split_front_matter(p.read_text(encoding="utf-8"))
        title = meta.get("title") or h1_of(body) or p.stem
        rel = p.relative_to(ROOT).as_posix()
        lines.append(f"- [{title}]({RAW}{quote(rel)}): {first_line(body)}")
    return "\n".join(lines) + "\n"


def h3_sections(rels: list[str]) -> str:
    parts = []
    for rel in rels:
        text = skill_text(rel)
        parts.append(f"### {describe(Path(rel).name, text)}\n\n{demote(text, 3)}")
    return "\n".join(parts)


def json_block(rel: str) -> str:
    return "```json\n" + (SKILL / rel).read_text(encoding="utf-8").strip() + "\n```"


def header(name: str, title: str, what: str, extra: str = "") -> str:
    others = [f"- [{other}]({RAW}{other}): {role}" for other, role in FILE_ROLE.items() if other != name]
    parts = [f"# {title} (v{project_version()})", f"> {what}"]
    if extra:
        parts.append(extra)
    parts += ["Bộ file cùng phiên bản:\n" + "\n".join(others),
              "File này sinh tự động từ `skills/sony-alpha-viet/`, `data-sample/` và `portable/system-prompt.md` "
              "bởi `scripts/build_portable.py`. Không sửa tay."]
    return "\n\n".join(parts)


def assemble(head: str, sections: list[tuple[str, str]]) -> str:
    numbered = [(f"{i}. {label}", body) for i, (label, body) in enumerate(sections, 1)]
    toc = "\n".join(f"- [{heading}](#{slug(heading)})" for heading, _ in numbered)
    blocks = [head, "## Mục lục\n\n" + toc,
              *[f"## {heading}\n\n{body.strip()}" for heading, body in numbered]]
    return "\n\n".join(blocks) + "\n"


def render_full() -> str:
    glossary, _ = rule_glossary(load("data-sample/glossary.json"))
    exceptions = load("data-sample/exceptions.json")
    rules = load("data-sample/rules.json")
    sections = [
        ("Vai trò và giọng điệu", demote(read("portable/system-prompt.md"), 2)),
        ("Quy tắc dịch menu", demote(skill_text("references/sony-menu-terms.md"), 2)),
        ("Văn phong tiếng Việt", demote(skill_text("references/writing-style-vi.md"), 2)),
        (f"Bảng thuật ngữ: {len(glossary)} mục", glossary_section(glossary)),
        ("Giữ nguyên tiếng Anh", keep_english_md(load("data-sample/keep_english.json"))),
        ("Ngoại lệ không dịch", exceptions_md(exceptions)),
        ("Quy tắc thay thế và từ cấm", rules_md(rules)),
        ("Ví dụ dịch", h3_sections(["examples/example-menu-translation.md", "examples/example-doc-translation.md"])),
    ]
    routing = "\n".join([
        "**Chọn mục theo việc**",
        "",
        "| Việc | Đọc |",
        "|---|---|",
        "| Dịch menu máy ảnh, dịch tài liệu, hỏi thông số hoặc giá | file này |",
        f"| Viết blog SEO/AIO | [llms-blog.txt]({RAW}llms-blog.txt) |",
        f"| Kiến thức, đào tạo, giáo án | [llms-knowledge.txt]({RAW}llms-knowledge.txt) |",
        "",
        "Thông số và giá: đối chiếu nguồn Sony chính thức, không đoán. Chưa kiểm chứng ghi [cần xác minh].",
        f"API công khai chỉ đọc (tùy chọn): `GET {API}/v1/lookup_term?text=Focus%20Area` tra một thuật ngữ; "
        f"`GET {API}/v1` liệt kê công cụ và tham số.",
    ])
    head = header(FULL.name, "Sony Alpha Việt: quy tắc lõi cho AI",
                  "Quy tắc dịch menu máy ảnh Sony EN/JP sang tiếng Việt, dịch tài liệu Sony và bảng thuật ngữ. "
                  "Không cần MCP. Đọc hết file này rồi làm theo vai trò ở mục 1.", routing)
    return assemble(head, sections)


def render_blog() -> str:
    sections = [
        ("Nguyên tắc bảo vệ Sony", demote(skill_text("references/sony-core-principles.md"), 2)),
        ("Checklist SEO và AIO 40 tiêu chí", demote(skill_text("references/seo-aio-checklist.md"), 2)),
        ("Khung bài blog", demote(skill_text("templates/blog-post-template.md"), 2)),
        ("Mẫu JSON-LD Article và FAQPage", json_block("templates/faq-schema.json")),
        ("Ví dụ bài blog", h3_sections(["examples/example-blog-post.md"])),
        ("Quy tắc đăng ColorLab", demote(skill_text("references/colorlab-vi.md"), 2)),
    ]
    head = header(BLOG.name, "Sony Alpha Việt: viết blog SEO/AIO",
                  "Quy tắc viết blog SEO/AIO cho Sony Alpha Việt: bảo vệ Sony, checklist 40 tiêu chí, khung bài, "
                  "FAQ schema, quy tắc đăng ColorLab.",
                  f"Đọc [llms-full.txt]({RAW}llms-full.txt) trước: bài blog dựa vào vai trò, văn phong và bảng "
                  "thuật ngữ ở đó.")
    return assemble(head, sections)


def render_knowledge() -> str:
    sections = [
        ("Vai trò trainer", demote(skill_text("references/trainer-vi.md"), 2)),
        ("Kiến thức nền", knowledge_section(knowledge_notes())),
    ]
    head = header(KNOWLEDGE.name, "Sony Alpha Việt: đào tạo và kiến thức nền",
                  "Vai trò trainer và kiến thức nền để trả lời học viên và soạn giáo án.",
                  f"Đọc [llms-full.txt]({RAW}llms-full.txt) trước khi dùng kiến thức này để dịch hoặc viết.")
    return assemble(head, sections)


def render_glossary_file() -> str:
    glossary, _ = rule_glossary(load("data-sample/glossary.json"))
    return "# Bảng thuật ngữ đầy đủ\n\n" + GLOSSARY_NOTE + "\n\n" + glossary_md(glossary, 2)


def portable_files() -> dict[str, str]:
    files = {Path(rel).name: skill_text(rel) for rel in FILES}
    files["glossary-full.md"] = render_glossary_file()
    return files


def render_index(knowledge: dict[str, str]) -> str:
    def item(path: str, text: str) -> str:
        return f"- [{Path(path).name}]({RAW}{quote(path)}): {describe(Path(path).name, text)}"

    lines = [
        "# Sony Alpha Việt",
        "",
        "> Skill và MCP dịch menu máy ảnh Sony EN/JP sang tiếng Việt, viết blog SEO/AIO theo quy tắc của dự án. "
        "Không có MCP vẫn dùng được: đưa link llms-full.txt cho bất kỳ AI nào.",
        "",
        "## Core",
        "",
        f"- [llms-full.txt]({RAW}llms-full.txt): {FILE_ROLE['llms-full.txt']}",
        "",
        "## Blog",
        "",
        f"- [llms-blog.txt]({RAW}llms-blog.txt): {FILE_ROLE['llms-blog.txt']}",
        "",
        "## Knowledge",
        "",
        f"- [llms-knowledge.txt]({RAW}llms-knowledge.txt): {FILE_ROLE['llms-knowledge.txt']}",
        "",
        "## Individual files",
        "",
        item("portable/system-prompt.md", read("portable/system-prompt.md")),
        item("AGENTS.md", read("AGENTS.md")),
        item("skills/sony-alpha-viet/SKILL.md", read("skills/sony-alpha-viet/SKILL.md")),
        *[item(f"portable/knowledge/{name}", knowledge[name]) for name in sorted(knowledge)],
        "",
        "## API công khai",
        "",
        f"- Gốc: {API} (chỉ đọc)",
        f"- `GET {API}/v1`: danh sách công cụ và tham số",
        f"- `GET {API}/v1/<tên>?…` hoặc `POST {API}/v1/<tên>` với JSON",
        f"- MCP: {API}/mcp",
    ]
    return "\n".join(lines) + "\n"


def build() -> dict[Path, str]:
    knowledge = portable_files()
    files = {OUT / name: text for name, text in knowledge.items()}
    files[FULL] = render_full()
    files[BLOG] = render_blog()
    files[KNOWLEDGE] = render_knowledge()
    files[INDEX] = render_index(knowledge)
    return files


def check(files: dict[Path, str]) -> int:
    stale = [p for p, text in files.items() if not p.is_file() or p.read_bytes() != text.encode("utf-8")]
    if OUT.is_dir():
        wanted = {p.name for p in files if p.parent == OUT}
        stale += [p for p in OUT.iterdir() if p.name not in wanted]
    if stale:
        for p in sorted(stale):
            print(f"lệch hoặc thừa: {p.relative_to(ROOT)}", file=sys.stderr)
        print("Chạy: uv run python scripts/build_portable.py", file=sys.stderr)
        return 1
    print(f"Các file sinh tự động khớp ({len(files)} file).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="không ghi file; thoát 1 nếu file trên đĩa khác bản sinh ra")
    args = parser.parse_args()
    files = build()
    if args.check:
        return check(files)
    if OUT.exists():
        shutil.rmtree(OUT)
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    knowledge = sum(1 for p in files if p.parent == OUT)
    n = len(read("portable/system-prompt.md"))
    print(f"{knowledge} file → {OUT.relative_to(ROOT)}; system-prompt.md {n} ký tự"
          + (" (VƯỢT 8.000 của Custom GPT!)" if n > PROMPT_LIMIT else ""))
    m = len(read("portable/meta-ai-studio/instructions.md").strip())
    print(f"meta-ai-studio/instructions.md {m} ký tự" + (" (VƯỢT 2.000 của Meta AI Studio!)" if m > META_LIMIT else ""))
    _, rewritten = rule_glossary(load("data-sample/glossary.json"))
    print(f"glossary: {len(rewritten)} mục đã áp quy tắc thay thế (ghi trong Ghi chú)")
    for path in (FULL, BLOG, KNOWLEDGE, INDEX):
        text = files[path]
        size = len(text.encode("utf-8"))
        warn = " (VƯỢT mục tiêu 90 KB của lõi!)" if path == FULL and size > CORE_LIMIT else ""
        print(f"{path.name}: {size} byte, {text.count(chr(10))} dòng{warn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
