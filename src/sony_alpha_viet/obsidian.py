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
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from . import blog, core, memory, paths

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "sony-alpha-viet"
TERM_TAG = "sony-alpha-viet/thuat-ngu"
UNSAFE = re.compile(r'[\\/:*?"<>|#^\[\]]')


# ---------------- config + note io ----------------
def vault_dir() -> Path:
    """<vault>/<vault_folder>; raises if no vault is configured."""
    cfg = {}
    if paths.CONFIG.exists():
        try:
            cfg = json.loads(paths.CONFIG.read_text(encoding="utf-8"))
        except ValueError:
            pass
    vault = os.environ.get("SONY_VN_VAULT") or cfg.get("vault")
    if not vault:
        raise RuntimeError(f"Chưa cấu hình vault: thêm \"vault\" vào {paths.CONFIG} hoặc đặt SONY_VN_VAULT")
    return Path(vault).expanduser() / cfg.get("vault_folder", "AI Skills/Sony Alpha Việt")


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
    keep = {k["term"].lower() for k in store.keep}
    terms = [g for g in store.glossary if g.get("locked") or g["en"].lower() in keep]
    names = {g["en"]: note_name(g["en"]) for g in terms}
    written, skipped = 0, []
    for g in terms:
        path = root / "Thuật ngữ" / f"{names[g['en']]}.md"
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
            body += ["", "## Liên quan", ""] + [f"- [[Thuật ngữ/{names[o['en']]}|{o['en']}]] → {o['vi']}" for o in related]
        write_note(path, _term_props(g, keep), "\n".join(body))
        written += 1

    idx = [f"- [[Thuật ngữ/{names[g['en']]}|{g['en']}]] → {g['vi']}" + (" · giữ tiếng Anh" if g["en"].lower() in keep else "")
           for g in sorted(terms, key=lambda g: g["en"].lower())]
    write_note(root / "Danh sách thuật ngữ.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
               f"# Thuật ngữ khóa ({len(terms)})\n\nMở một note để xem ví dụ và sửa. Tạo thuật ngữ mới: thêm note vào `Thuật ngữ/` "
               "với thuộc tính `en`, `vi` (tùy chọn `short`, `locked`, `note`), rồi import.\n\n" + "\n".join(idx))

    rows = ["| EN | VI | Ngắn | Khóa | Ghi chú |", "|---|---|---|---|---|"]
    for g in store.glossary:
        en = f"[[Thuật ngữ/{names[g['en']]}\\|{g['en']}]]" if g["en"] in names else g["en"]
        cell = lambda s: str(s or "").replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {en} | {cell(g['vi'])} | {cell(g.get('short'))} | {'🔒' if g.get('locked') else ''} | {cell(g.get('note'))} |")
    write_note(root / "Bảng thuật ngữ.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
               f"# Bảng thuật ngữ menu ({len(store.glossary)})\n\nBảng sinh tự động từ `glossary.json`, đừng sửa ở đây. "
               f"Thuật ngữ khóa có note riêng (xem [[Danh sách thuật ngữ]]), sửa ở đó.\n\n" + "\n".join(rows))

    keep_rows = [f"- **{k['term']}** — thay cho: {', '.join(k.get('vi_variants', {}))} — {k.get('why', '')}" for k in store.keep]
    write_note(root / "Giữ tiếng Anh.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
               "# Thuật ngữ giữ tiếng Anh\n\nGiữ khi bản tiếng Việt không giúp người dùng hiểu hơn. Viết hoa theo bản gốc.\n\n"
               + ("\n".join(keep_rows) or "_Chưa có._"))

    log = core.DATA / "LEARNING_LOG.md"
    write_note(root / "Nhật ký học.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"]},
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
    write_note(root / "Rà soát nhất quán.md", {"generated": True, "updated": _today(), "groups": len(rep), "tags": ["sony-alpha-viet"]},
               "\n".join(lines))

    for src in sorted(SKILL.rglob("*")):
        if src.is_file():
            rel = src.relative_to(SKILL)
            text = src.read_text(encoding="utf-8")
            if src.suffix != ".md":
                text = f"# {rel}\n\n```{src.suffix.lstrip('.')}\n{text.rstrip()}\n```"
            dest = root / "Skill" / rel.with_suffix(".md")
            write_note(dest, {"generated": True, "source": f"skills/sony-alpha-viet/{rel}", "updated": _today()},
                       "> Bản sao chỉ đọc. Sửa ở repo `thaikpham-blogskill` rồi export lại.\n\n" + re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S))
    template = (SKILL / "templates" / "blog-post-template.md").read_text(encoding="utf-8")
    (root / "Mẫu").mkdir(parents=True, exist_ok=True)
    (root / "Mẫu" / "Bài blog SEO.md").write_text(template, encoding="utf-8")
    (root / "Blog").mkdir(exist_ok=True)

    info = {"tm": len(store.tm), "terms": len(store.glossary), "locked": sum(1 for g in store.glossary if g.get("locked")),
            "keep_english": len(store.keep), "data": str(core.DATA)}
    write_note(root / "Sony Alpha Việt.md", {"generated": True, "updated": _today(), "tags": ["sony-alpha-viet"], **info}, f"""
# Sony Alpha Việt

Trang chủ dữ liệu dịch và viết blog Sony Alpha. Các note ở đây do skill `sony-alpha-viet` sinh ra (lần cuối {_today()}).

| Mục | Dùng để |
|---|---|
| [[Danh sách thuật ngữ]] | {len(terms)} thuật ngữ khóa / giữ tiếng Anh. **Sửa được**, rồi nhập lại vào bộ nhớ |
| [[Bảng thuật ngữ]] | Toàn bộ {info['terms']} thuật ngữ (chỉ đọc) |
| [[Giữ tiếng Anh]] | Thuật ngữ không dịch |
| [[Rà soát nhất quán]] | {len(rep)} chuỗi có nhiều bản dịch cần quyết định |
| [[Nhật ký học]] | Những gì công cụ đã tự học |
| [[Skill/SKILL\\|Skill]] | Quy tắc, glossary, checklist SEO/AIO (bản sao chỉ đọc) |
| Blog/ | Bản nháp bài viết; mẫu ở [[Mẫu/Bài blog SEO]] |

Bộ nhớ dịch: {info['tm']} chuỗi · dữ liệu: `{info['data']}`

## Cách dùng với Claude / Gemini
- "Export Obsidian": cập nhật các note này từ bộ nhớ.
- Sửa note trong `Thuật ngữ/` (thuộc tính `vi`, `short`, `locked`) hoặc tạo note mới cùng thuộc tính `en`, `vi` → "Import thuật ngữ từ Obsidian".
- Viết nháp trong `Blog/` theo mẫu → "Audit SEO note Blog/<tên>": kết quả ghi vào thuộc tính `seo_*` và note `… — SEO audit`.
""")
    return {"vault_dir": str(root), "term_notes_written": written, "skipped_pending_edits": skipped,
            "consistency_groups": len(rep), "glossary_rows": len(store.glossary)}


# ---------------- import ----------------
def import_terms(store: core.Store, apply: bool = False) -> dict:
    """Read term notes (edited or newly created in Obsidian) and turn differences into glossary decisions."""
    folder = vault_dir() / "Thuật ngữ"
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
    im = sub.add_parser("import", help="đưa thuật ngữ sửa trong Obsidian vào bộ nhớ")
    im.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ xem trước)")
    au = sub.add_parser("audit", help="chấm SEO/AIO một note blog")
    au.add_argument("path")
    au.add_argument("--keyword", default="")
    a = ap.parse_args()
    store = core.Store()
    out = export(store) if a.cmd == "export" else import_terms(store, a.apply) if a.cmd == "import" else audit_note(a.path, a.keyword)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
