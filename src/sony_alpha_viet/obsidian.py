"""Obsidian vault integration: browse/curate terminology as notes, review consistency, audit blog drafts in place.

Vault location comes from ~/.config/sony-alpha-viet/config.json: {"vault": "...", "vault_folder": "AI Skills/Sony Alpha Việt"}
(or SONY_VN_VAULT). Everything is plain Markdown + YAML properties, so it works with Obsidian closed and without plugins.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from . import blog, core, docs, knowledge, memory, paths

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "sony-alpha-viet"
TERM_TAG = "sony-alpha-viet/thuat-ngu"
UNSAFE = re.compile(r'[\\/:*?"<>|#^\[\]]')

# Vault tree (numbered = reading order). 1–2 mirror <data>/knowledge/ 1:1; the rest is generated or user drafts.
KB_DIRS = ("1 Kiến thức", "2 Giáo án")
TERMS = "3 Thuật ngữ"
MENU = "4 Dịch menu"
DOCS = "5 Tài liệu Sony"
BLOG = "6 Blog"
SKILL_COPY = "9 Skill"
LEGACY = [("Thuật ngữ", TERMS), ("Danh sách thuật ngữ.md", f"{TERMS}/Danh sách thuật ngữ.md"),
          ("Bảng thuật ngữ.md", f"{TERMS}/Bảng thuật ngữ.md"), ("Giữ tiếng Anh.md", f"{TERMS}/Giữ tiếng Anh.md"),
          ("Rà soát nhất quán.md", f"{MENU}/Rà soát nhất quán.md"), ("Nhật ký học.md", f"{MENU}/Nhật ký học.md"),
          ("Dự án ILDC", f"{MENU}/Dự án ILDC"), ("Tài liệu Sony", DOCS), ("Blog", BLOG), ("Mẫu", f"{BLOG}/Mẫu"), ("Skill", SKILL_COPY)]


# ---------------- config + note io ----------------
def _cfg() -> dict:
    try:
        return json.loads(paths.CONFIG.read_text(encoding="utf-8")) if paths.CONFIG.exists() else {}
    except ValueError:
        return {}


def _vault() -> Path:
    vault = os.environ.get("SONY_VN_VAULT") or _cfg().get("vault")
    if not vault:
        raise RuntimeError(f"Chưa cấu hình vault: thêm \"vault\" vào {paths.CONFIG} hoặc đặt SONY_VN_VAULT")
    return Path(vault).expanduser()


def vault_dir() -> Path:
    """<vault>/<vault_folder>; raises if no vault is configured."""
    return _vault() / _cfg().get("vault_folder", "AI Skills/Sony Alpha Việt")


def kb_dir() -> Path:
    """Where 1 Kiến thức/ and 2 Giáo án/ live: <vault>/<knowledge_folder> if configured (e.g. a separate wiki), else vault_dir()."""
    sub = _cfg().get("knowledge_folder")
    return _vault() / sub if sub else vault_dir()


def _today() -> str:
    return _dt.date.today().isoformat()


def note_name(en: str) -> str:
    return UNSAFE.sub("-", en).strip(" .") or "term"


def write_note(path: Path, props: dict, body: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = yaml.safe_dump(props, allow_unicode=True, sort_keys=False, width=10**6).strip()
    path.write_text(f"---\n{fm}\n---\n\n{body.strip()}\n", encoding="utf-8")


def read_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    try:
        props = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        props = {}
    return (props if isinstance(props, dict) else {}), text[m.end():]


def upsert_props(path: Path, updates: dict):
    """Set some properties on an existing note, keeping its other properties and body."""
    props, body = read_note(path)
    props.update(updates)
    write_note(path, props, body)


def migrate(root: Path) -> dict:
    """Move notes from the old flat layout into the numbered tree. Never overwrites; idempotent."""
    moved, conflicts = [], []
    def move(src: Path, dst: Path):
        if src.is_dir():
            for child in sorted(src.iterdir()):
                move(child, dst / child.name)
            if not any(src.iterdir()):
                src.rmdir()
        elif dst.exists():
            if src.read_bytes() == dst.read_bytes():
                src.unlink()
            else:
                conflicts.append(str(src.relative_to(root)))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append(f"{src.relative_to(root)} → {dst.relative_to(root)}")
    for old, new in LEGACY:
        if (root / old).exists():
            move(root / old, root / new)
    return {"moved": moved, "conflicts": conflicts}


# ---------------- consistency ----------------
def consistency_report(store: core.Store, limit: int = 200) -> list[dict]:
    """Same English source translated differently in the translation memory (icons ignored), biggest groups first."""
    groups = defaultdict(lambda: defaultdict(list))
    for t in store.tm:
        vi = re.sub(r"\s+", " ", core.TOKEN_RE.sub("", t["vi"])).strip()  # icons/variables anywhere don't count
        groups[core._key(t["en"])][vi].append((t.get("id", ""), str(t.get("maxW") or "")))
    out = []
    for key, variants in groups.items():
        if len({core.nfc(v).lower() for v in variants}) < 2:
            continue
        en = next(t["en"] for t in store.tm if core._key(t["en"]) == key)
        out.append({"en": re.sub(r"\s+", " ", core.TOKEN_RE.sub("", en)).strip(), "variants": [
            {"vi": v, "count": len(rows), "ids": [i for i, _ in rows][:6],
             "max_widths": sorted({int(w) for _, w in rows if w.isdigit()})} for v, rows in sorted(variants.items(), key=lambda x: -len(x[1]))]})
    out.sort(key=lambda g: -sum(v["count"] for v in g["variants"]))
    return out[:limit]


# ---------------- export ----------------
def _term_props(g: dict, keep: set[str]) -> dict:
    p = {"en": g["en"], "vi": g["vi"], "short": g.get("short") or g["vi"], "locked": bool(g.get("locked")),
         "category": g.get("category", ""), "keep_english": g["en"].lower() in keep, "tags": [TERM_TAG]}
    if g.get("note"):
        p["note"] = g["note"]
    return p


def _differs(props: dict, g: dict) -> bool:
    return (str(props.get("vi", "")).strip() != g["vi"] or str(props.get("short", "")).strip() != (g.get("short") or g["vi"])
            or bool(props.get("locked")) != bool(g.get("locked")))


def export(store: core.Store) -> dict:
    """Write/refresh generated notes. Term notes the user edited but hasn't imported yet are left untouched."""
    root = vault_dir()
    mig = migrate(root)
    keep = {k["term"].lower() for k in store.keep}
    terms = [g for g in store.glossary if g.get("locked") or g["en"].lower() in keep]
    names = {g["en"]: note_name(g["en"]) for g in terms}
    written, skipped = 0, []
    for g in terms:
        path = root / TERMS / f"{names[g['en']]}.md"
        if path.exists():
            props, _ = read_note(path)
            if props.get("en") == g["en"] and _differs(props, g):
                skipped.append(g["en"])  # pending user edit → import first
                continue
        rx = re.compile(r"(?<![a-z])" + re.escape(g["en"].lower()) + r"(?![a-z])")
        examples = [t for t in store.tm if rx.search(t["en"].lower())][:6]
        related = [o for o in terms if o is not g and (g["en"].lower() in o["en"].lower() or o["en"].lower() in g["en"].lower())][:10]
        body = [f"# {g['en']} → {g['vi']}", ""]
        if g.get("note"):
            body += [f"> {g['note']}", ""]
        body += ["Sửa thuộc tính `vi`, `short`, `locked` ở trên rồi chạy **obsidian_import** để đưa vào bộ nhớ.", "",
                 "## Ví dụ trong bộ nhớ dịch", ""]
        body += [f"- `{t.get('id', '')}` `{t['en']}` → `{t['vi']}`" for t in examples] or ["_Chưa có._"]
        if related:
            body += ["", "## Liên quan", ""] + [f"- [[{TERMS}/{names[o['en']]}|{o['en']}]] → {o['vi']}" for o in related]
        write_note(path, _term_props(g, keep), "\n".join(body))
        written += 1

    idx = [f"- [[{TERMS}/{names[g['en']]}|{g['en']}]] → {g['vi']}" + (" · giữ tiếng Anh" if g["en"].lower() in keep else "")
           for g in sorted(terms, key=lambda g: g["en"].lower())]
    write_note(root / TERMS / "Danh sách thuật ngữ.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
               f"# Thuật ngữ khóa ({len(terms)})\n\nMở một note để xem ví dụ và sửa. Tạo thuật ngữ mới: thêm note vào `{TERMS}/` "
               "với thuộc tính `en`, `vi` (tùy chọn `short`, `locked`, `note`), rồi import.\n\n" + "\n".join(idx))

    rows = ["| EN | VI | Ngắn | Khóa | Ghi chú |", "|---|---|---|---|---|"]
    for g in store.glossary:
        en = f"[[{TERMS}/{names[g['en']]}\\|{g['en']}]]" if g["en"] in names else g["en"]
        cell = lambda s: str(s or "").replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {en} | {cell(g['vi'])} | {cell(g.get('short'))} | {'🔒' if g.get('locked') else ''} | {cell(g.get('note'))} |")
    write_note(root / TERMS / "Bảng thuật ngữ.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
               f"# Bảng thuật ngữ menu ({len(store.glossary)})\n\nBảng sinh tự động từ `glossary.json`, đừng sửa ở đây. "
               f"Thuật ngữ khóa có note riêng (xem [[Danh sách thuật ngữ]]), sửa ở đó.\n\n" + "\n".join(rows))

    keep_rows = [f"- **{k['term']}** — thay cho: {', '.join(k.get('vi_variants', {}))} — {k.get('why', '')}" for k in store.keep]
    write_note(root / TERMS / "Giữ tiếng Anh.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
               "# Thuật ngữ giữ tiếng Anh\n\nGiữ khi bản tiếng Việt không giúp người dùng hiểu hơn. Viết hoa theo bản gốc.\n\n"
               + ("\n".join(keep_rows) or "_Chưa có._"))

    log = core.DATA / "LEARNING_LOG.md"
    write_note(root / MENU / "Nhật ký học.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
               log.read_text(encoding="utf-8") if log.exists() else "# Nhật ký tự học\n\n_Chưa có._")

    rep = consistency_report(store)
    lines = ["# Rà soát nhất quán", "",
             f"{len(rep)} chuỗi tiếng Anh đang có nhiều bản dịch trong bộ nhớ (đã bỏ qua khác biệt icon). "
             "Bản ngắn hơn ở khung hẹp hơn thường là rút gọn hợp lệ; ngữ cảnh khác cũng có thể cần bản khác (Active = Chủ động / Hoạt động). "
             "Số còn lại nên thống nhất. "
             "Đánh dấu bản muốn giữ rồi nhờ Claude áp dụng.", ""]
    for gr in rep:
        lines.append(f"## {gr['en']}")
        lines += [f"- [ ] `{v['vi']}` — {v['count']} chuỗi" + (f", khung {'/'.join(map(str, v['max_widths']))}px" if v["max_widths"] else "")
                  + f" ({', '.join(i for i in v['ids'] if i)})" for v in gr["variants"]]
        lines.append("")
    write_note(root / MENU / "Rà soát nhất quán.md", {"generated": True, "updated": _today(), "groups": len(rep), "tags": ["sony-alpha-viet"]},
               "\n".join(lines))

    for src in sorted(SKILL.rglob("*")):
        if src.is_file():
            rel = src.relative_to(SKILL)
            text = src.read_text(encoding="utf-8")
            if src.suffix != ".md":
                text = f"# {rel}\n\n```{src.suffix.lstrip('.')}\n{text.rstrip()}\n```"
            dest = root / SKILL_COPY / rel.with_suffix(".md")
            write_note(dest, {"generated": True, "source": f"skills/sony-alpha-viet/{rel}", "updated": _today()},
                       "> Bản sao chỉ đọc. Sửa ở repo `alphaskill` rồi export lại.\n\n" + re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S))
    template = (SKILL / "templates" / "blog-post-template.md").read_text(encoding="utf-8")
    (root / BLOG / "Mẫu").mkdir(parents=True, exist_ok=True)
    (root / BLOG / "Mẫu" / "Bài blog SEO.md").write_text(template, encoding="utf-8")

    doc_info = export_docs(store)
    kb = export_knowledge(kb_dir())
    lessons = sum(1 for n in knowledge.load() if n["path"].startswith(KB_DIRS[1]))
    info = {"knowledge": kb["notes"], "tm": len(store.tm), "terms": len(store.glossary),
            "locked": sum(1 for g in store.glossary if g.get("locked")), "keep_english": len(store.keep), "data": str(core.DATA)}
    write_note(root / "Sony Alpha Việt.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"], **info}, f"""
# Sony Alpha Việt — bộ não thứ hai của Sony Camera Trainer

Kiến thức để dạy, giáo án để đứng lớp, thuật ngữ và bộ nhớ dịch menu, tài liệu Sony, bản nháp blog. Note sinh tự động bởi skill
`sony-alpha-viet` (lần cuối {_today()}); kiến thức và giáo án sửa thẳng ở đây được.

| Mục | Dùng để |
|---|---|
| [[Kiến thức\\|1 Kiến thức]] | {kb["notes"] - lessons} note nhiếp ảnh: phơi sáng, lấy nét, màu, bố cục, kỹ thuật sáng tạo, quy trình. **Sửa được** |
| [[Giáo án\\|2 Giáo án]] | {lessons} khóa học, bài thực hành, cài đặt nhanh, đính chính slide. **Sửa được** |
| [[{TERMS}/Danh sách thuật ngữ\\|3 Thuật ngữ]] | {len(terms)} thuật ngữ khóa (sửa được) · [[{TERMS}/Bảng thuật ngữ\\|bảng {info['terms']} thuật ngữ]] · [[{TERMS}/Giữ tiếng Anh\\|giữ tiếng Anh]] |
| [[{MENU}/Rà soát nhất quán\\|4 Dịch menu]] | {len(rep)} chuỗi nhiều bản dịch · [[{MENU}/Nhật ký học\\|nhật ký tự học]] · dự án ILDC |
| [[{DOCS}/Tài liệu Sony\\|5 Tài liệu Sony]] | {doc_info.get('docs', 0)} tài liệu tiếng Việt chính thức + đối chiếu thuật ngữ |
| {BLOG}/ | Bản nháp bài viết; mẫu ở [[{BLOG}/Mẫu/Bài blog SEO\\|Mẫu bài blog SEO]] |
| [[{SKILL_COPY}/SKILL\\|9 Skill]] | Quy tắc, glossary, checklist SEO/AIO (bản sao chỉ đọc) |

Bộ nhớ dịch: {info['tm']} chuỗi · dữ liệu: `{info['data']}`

## Hỏi Claude thế nào
- **Dạy học:** "học viên hỏi vì sao ảnh áo cưới bị xám" → `search_knowledge`; "mở giáo án Photo Basic" → `get_knowledge`;
  "lưu câu hỏi này vào note Bù sáng" → `add_knowledge`. Sửa note trong 1–2 rồi "import Obsidian" để đưa về kho dữ liệu.
- **Dịch menu:** "dịch các chuỗi này" (prepare_batch → check_translation) · "rà cả thư mục output" → `xls_review`.
- **Thuật ngữ:** sửa note trong `{TERMS}/` → "import Obsidian".
- **Blog:** viết nháp trong `{BLOG}/` → "audit SEO note {BLOG}/<tên>".
- "Export Obsidian": làm mới toàn bộ cây này từ kho dữ liệu (note bạn đang sửa dở không bị ghi đè).
""")
    return {"vault_dir": str(root), "migrated": mig, "knowledge": kb, "term_notes_written": written, "skipped_pending_edits": skipped,
            "consistency_groups": len(rep), "glossary_rows": len(store.glossary), "sony_docs": doc_info.get("docs", 0)}


# ---------------- knowledge mirror ----------------
def _kb_text(props: dict, body: str) -> str:
    return knowledge.join_note({k: v for k, v in props.items() if k != "kb_hash"}, body)


def _kb_state(path: Path) -> str:
    """'new' (created in Obsidian), 'edited' (changed since export), 'clean', or 'generated'."""
    props, body = read_note(path)
    if props.get("generated"):
        return "generated"
    if "kb_hash" not in props:
        return "new"
    return "clean" if knowledge.sha1(_kb_text(props, body)) == props["kb_hash"] else "edited"


def export_knowledge(root: Path) -> dict:
    """Mirror <data>/knowledge/ into the vault (kb_hash marks our copy); user edits are kept; index note per top folder."""
    notes, written, pending, removed = knowledge.load(), 0, [], []
    have = {n["path"] for n in notes}
    for n in notes:
        dest = root / n["path"]
        if dest.exists() and _kb_state(dest) in ("edited", "new"):
            pending.append(n["path"])
            continue
        text = _kb_text(n["props"], n["body"])
        props, body = knowledge.split_note(text)
        write_note(dest, {**props, "kb_hash": knowledge.sha1(text)}, body)
        written += 1
    for top in KB_DIRS:
        for f in sorted((root / top).rglob("*.md")) if (root / top).exists() else []:
            rel = f.relative_to(root).as_posix()
            if rel not in have and _kb_state(f) == "clean":  # renamed/removed in data, untouched in vault
                f.unlink()
                removed.append(rel)
        title = top.split(" ", 1)[1]
        groups = defaultdict(list)
        for n in notes:
            if n["path"].startswith(top + "/"):
                sub = "/".join(Path(n["path"]).parts[1:-1]) or title
                groups[sub].append(f"- [[{n['title']}]] — {n['summary']}")
        lines = [f"# {title}", "", "Sinh tự động từ kho kiến thức; sửa note con, đừng sửa trang này.", ""]
        for sub in sorted(groups):
            lines += [f"## {sub}", "", *groups[sub], ""]
        write_note(root / top / f"{title}.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]}, "\n".join(lines))
    return {"dir": str(root), "notes": len(notes), "written": written, "pending_edits": pending, "removed": removed}


def import_knowledge(apply: bool = False) -> dict:
    """Knowledge notes edited or created in the vault → back into <data>/knowledge/ (apply=True); preview otherwise."""
    root, changes = kb_dir(), []
    for top in KB_DIRS:
        for f in sorted((root / top).rglob("*.md")) if (root / top).exists() else []:
            state = _kb_state(f)
            if state in ("edited", "new"):
                changes.append({"path": f.relative_to(root).as_posix(), "kind": state})
    if apply:
        for c in changes:
            props, body = read_note(root / c["path"])
            text = _kb_text(props, body)
            dest = knowledge.root() / c["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            p2, b2 = knowledge.split_note(text)
            write_note(root / c["path"], {**p2, "kb_hash": knowledge.sha1(text)}, b2)
    return {"changes": changes, "applied": apply and bool(changes)}


def import_all(store: core.Store, apply: bool = False) -> dict:
    return {"terms": import_terms(store, apply), "knowledge": import_knowledge(apply)}


def export_docs(store: core.Store) -> dict:
    """Tài liệu Sony/: one note per ingested document, an index with Help Guide links, and the glossary-vs-Sony report."""
    corpus = docs.load()
    if not corpus["docs"]:
        return {"docs": 0}
    root = vault_dir() / DOCS
    locked = [g for g in store.glossary if g.get("locked") and len(g["vi"]) >= 4]
    names = {}
    for m in corpus["docs"]:
        text = corpus["texts"].get(m["id"], "")
        name = f"{m['model']} — {m['kind']}"
        names[m["id"]] = name
        low = docs._fold(text)
        seen = [g for g in locked if re.search(r"(?<!\w)" + re.escape(docs._fold(g["vi"])) + r"(?!\w)", low)]
        terms = "\n".join(f"- [[{TERMS}/{note_name(g['en'])}|{g['en']}]] → {g['vi']}" for g in seen) or "_Không có._"
        write_note(root / f"{name}.md", {"model": m["model"], "kind": m["kind"], "code": m["code"], "pages": m["pages"],
                                          "source_file": m["file"], "encoding": m["encoding"], "language": "vi",
                                          "tags": ["sony-alpha-viet/tai-lieu"], "updated": _today()},
                   f"# {m['model']} — {m['kind']}\n\nBản chính thức tiếng Việt của Sony ({m['code'] or 'không mã'}, {m['pages']} trang"
                   + (", chuyển từ font VNI" if m["encoding"] == "vni" else "") + "). Văn bản trích từ PDF, hình minh họa không có.\n\n"
                   + text + "\n\n## Thuật ngữ khóa xuất hiện\n\n" + terms)
    rows = ["| Model | Tài liệu | Mã | Trang |", "|---|---|---|---|"] + [
        f"| {m['model']} | [[{DOCS}/{names[m['id']]}\\|{m['kind']}]] | {m['code']} | {m['pages']} |" for m in corpus["docs"]]
    links = [f"- [{l['title']}]({l['url']})" for l in corpus.get("links", [])]
    dup = [f"- `{d['file']}` trùng với `{d['same_as']}` (bỏ qua)" for d in corpus.get("duplicates", [])]
    write_note(root / "Tài liệu Sony.md", {"generated": True, "updated": _today(), "docs": len(corpus["docs"]), "tags": ["sony-alpha-viet"]},
               "# Tài liệu Sony chính thức\n\nNguồn đối chiếu cách Sony Việt Nam diễn đạt. Tìm bằng công cụ `search_docs` "
               "hoặc Obsidian search. Xem [[Đối chiếu thuật ngữ với Sony]].\n\n" + "\n".join(rows)
               + ("\n\n## Help Guide trực tuyến\n\n" + "\n".join(links) if links else "") + ("\n\n## File trùng\n\n" + "\n".join(dup) if dup else ""))
    r = docs.term_report(store)
    b = ["# Đối chiếu thuật ngữ với tài liệu Sony", "", f"So glossary và quy tắc với {r['docs']} tài liệu tiếng Việt chính thức của Sony. "
         "Đây là bằng chứng để bạn quyết định, công cụ không tự sửa gì.", "", "## Từ bị cấm nhưng Sony có dùng", ""]
    for x in r["banned_forms_sony_uses"]:
        models = ", ".join(f"{k} ({v})" for k, v in x["by_model"].items())
        b += [f"### `{x['sony_uses']}`", f"Quy tắc: {x['why']} · Sony dùng ở: {models}", ""] + [f"> {e}" for e in x["examples"][:2]] + [""]
    if not r["banned_forms_sony_uses"]:
        b.append("_Không có._")
    b += ["", "## Từ tiếng Anh Sony giữ trong văn bản tiếng Việt", "", "| Từ | Số lần | Số tài liệu |", "|---|---|---|"]
    b += [f"| {k['word']} | {k['count']} | {k['models']} |" for k in r["english_kept_by_sony"]]
    b += ["", "## Thuật ngữ khóa Sony có dùng", "", "| EN | VI | Số lần |", "|---|---|---|"]
    b += [f"| [[{TERMS}/{note_name(x['en'])}\\|{x['en']}]] | {x['vi']} | {x['count']} |" for x in r["locked_terms_used_by_sony"]]
    write_note(root / "Đối chiếu thuật ngữ với Sony.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]}, "\n".join(b))
    return {"docs": len(corpus["docs"]), "banned_forms_sony_uses": len(r["banned_forms_sony_uses"])}


# ---------------- import ----------------
def import_terms(store: core.Store, apply: bool = False) -> dict:
    """Read term notes (edited or newly created in Obsidian) and turn differences into glossary decisions."""
    migrate(vault_dir())
    folder = vault_dir() / TERMS
    changes = []
    for path in sorted(folder.glob("*.md")) if folder.exists() else []:
        props, _ = read_note(path)
        en, vi = str(props.get("en", "")).strip(), str(props.get("vi", "")).strip()
        if not en or not vi:
            continue
        short = str(props.get("short") or vi).strip()
        locked = bool(props.get("locked", True))
        g = store.gl_by_en.get(en.lower())
        if g and not _differs({"vi": vi, "short": short, "locked": locked}, g):
            continue
        changes.append({"note": path.name, "en": en, "old": {"vi": g["vi"], "short": g.get("short"), "locked": g.get("locked")} if g else None,
                        "new": {"vi": vi, "short": short, "locked": locked}, "note_text": str(props.get("note", "") or "")})
    if apply:
        for c in changes:
            memory.record_term(store, c["en"], c["new"]["vi"], c["new"]["short"], c["note_text"] or "sửa trong Obsidian", c["new"]["locked"])
    return {"changes": changes, "applied": apply and bool(changes)}


# ---------------- blog audit ----------------
def audit_note(path: str, primary_keyword: str = "") -> dict:
    """seo_audit a draft in the vault; write a sibling report note and seo_* properties on the draft."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = vault_dir() / p
    if p.suffix != ".md":
        p = p.with_suffix(".md")
    r = blog.seo_audit(p.read_text(encoding="utf-8"), primary_keyword)
    report = p.with_name(f"{p.stem} — SEO audit.md")
    rows = ["| # | Mục | Kết quả | Bằng chứng | Cách sửa |", "|---|---|---|---|---|"]
    for i in r["items"]:
        cell = lambda s: str(s or "").replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {i['id']}{'*' if i['required'] else ''} | {cell(i['item'])} | {i['status']} | {cell(i['evidence'])} | {cell(i['fix'])} |")
    write_note(report, {"audit_of": f"[[{p.stem}]]", "seo_score": r["score"], "seo_percent": r["score_percent"],
                        "seo_complete": r["complete"], "audited": _today(), "tags": ["sony-alpha-viet/audit"]},
               f"# SEO/AIO audit: [[{p.stem}]]\n\nĐiểm **{r['score']}** ({r['score_percent']}%) · "
               f"{'✅ đủ mục bắt buộc' if r['complete'] else '❌ còn mục bắt buộc: ' + ', '.join(map(str, r['required_failed']))}"
               f" · {r['words']} từ\n\n`*` = mục bắt buộc\n\n" + "\n".join(rows))
    upsert_props(p, {"seo_score": r["score"], "seo_complete": r["complete"], "seo_audited": _today()})
    return {"note": str(p), "report": str(report), "score": r["score"], "complete": r["complete"], "required_failed": r["required_failed"]}


def main():
    ap = argparse.ArgumentParser(prog="sony-alpha-viet-obsidian", description="Đồng bộ Sony Alpha Việt với vault Obsidian")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export", help="ghi/cập nhật note thuật ngữ, bảng, rà soát, bản sao skill")
    im = sub.add_parser("import", help="đưa thuật ngữ và kiến thức sửa trong Obsidian về kho dữ liệu")
    im.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ xem trước)")
    au = sub.add_parser("audit", help="chấm SEO/AIO một note blog")
    au.add_argument("path")
    au.add_argument("--keyword", default="")
    a = ap.parse_args()
    store = core.Store()
    out = export(store) if a.cmd == "export" else import_all(store, a.apply) if a.cmd == "import" else audit_note(a.path, a.keyword)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
