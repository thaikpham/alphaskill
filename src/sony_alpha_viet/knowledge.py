"""Trainer knowledge base: photography lessons and course plans as Markdown notes (YAML properties) under <data>/knowledge/.
Searchable from MCP (accent-insensitive, ranked by section) and mirrored into the Obsidian vault by obsidian.py."""
from __future__ import annotations

import difflib
import hashlib
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath

import yaml

from . import core

TAG = "sony-alpha-viet/kien-thuc"
SKIP_SECTIONS = {"liên quan"}  # link lists: noise for search


def root(data: Path | None = None) -> Path:
    return (data or core.DATA) / "knowledge"


def fold(text: str) -> str:
    """NFC, lower, no diacritics, đ→d: 'Khẩu độ' and 'khau do' fold to the same string."""
    t = unicodedata.normalize("NFD", core.nfc(text).lower().replace("đ", "d"))
    return re.sub(r"\s+", " ", "".join(c for c in t if unicodedata.category(c) != "Mn")).strip()


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def split_note(text: str) -> tuple[dict, str]:
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    try:
        props = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        props = {}
    return (props if isinstance(props, dict) else {}), text[m.end():]


def join_note(props: dict, body: str) -> str:
    fm = yaml.safe_dump(props, allow_unicode=True, sort_keys=False, width=10**6).strip()
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def _sections(title: str, body: str) -> list[dict]:
    parts = re.split(r"^## +(.+?)\s*$", body, flags=re.M)
    head = re.sub(r"^# .*$", "", parts[0], count=1, flags=re.M).strip()
    out = [{"heading": title, "text": head}] if head else []
    out += [{"heading": h.strip(), "text": t.strip()} for h, t in zip(parts[1::2], parts[2::2]) if t.strip()]
    return out


def _summary(body: str) -> str:
    m = re.search(r"\*\*(.+?)\*\*", body)
    s = m.group(1) if m else next((p for p in body.split("\n\n") if p.strip() and not p.startswith("#")), "")
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= 200 else s[:199] + "…"


def load(data: Path | None = None) -> list[dict]:
    """Every note: {path (posix, relative to knowledge/), title, props, body, summary, sections: [{heading, text}]}."""
    base = root(data)
    notes = []
    for f in sorted(base.rglob("*.md")) if base.exists() else []:
        props, body = split_note(f.read_text(encoding="utf-8"))
        title = str(props.get("title") or f.stem)
        notes.append({"path": f.relative_to(base).as_posix(), "title": title, "props": props, "body": body,
                      "summary": _summary(body), "sections": _sections(title, body)})
    return notes


def _names(n: dict) -> list[str]:
    return [n["title"], *[str(a) for a in (n["props"].get("aliases") or [])]]


def search(query: str, limit: int = 6, data: Path | None = None) -> list[dict]:
    """Sections ranked by BM25 over folded tokens + phrase bonus + title/alias bonus. [{note, title, section, score, text}]."""
    q = fold(query)
    terms = [t for t in re.findall(r"\w+", q) if len(t) >= 2]
    if not terms:
        return []
    docs = [(n, s, re.findall(r"\w+", fold(f'{n["title"]} {s["heading"]} {" ".join(map(str, n["props"].get("tags") or []))} {s["text"]}')))
            for n in load(data) for s in n["sections"] if s["heading"].lower() not in SKIP_SECTIONS]  # title/heading/tags count as text
    if not docs:
        return []
    df = Counter(t for _, _, toks in docs for t in set(toks))
    avg = sum(len(toks) for _, _, toks in docs) / len(docs)
    out = []
    for n, s, toks in docs:
        tf = Counter(toks)
        score = sum(math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5)) * tf[t] * 2.2 / (tf[t] + 1.2 * (0.5 + 0.5 * len(toks) / avg))
                    for t in terms if tf[t])
        if len(terms) > 1 and q in " ".join(toks):
            score += 3
        names = [fold(x) for x in _names(n)]
        if q in names or any(q in x or x in q for x in names if len(x) >= 3):  # "Aperture" finds Khẩu độ via its alias
            score += 4 + (2 if s["heading"] in (n["title"], "Hiểu nhanh") else 0)
        if score > 0:
            out.append({"note": n["path"], "title": n["title"], "section": s["heading"], "score": round(score, 2), "text": s["text"][:1200]})
    out.sort(key=lambda x: (-x["score"], x["note"], x["section"]))
    return out[:limit]


def tree(data: Path | None = None) -> dict:
    """Folder tree: {"count": n, "<folder>": {"<sub>": {...}, "_notes": [{title, path, summary}]}}."""
    notes = load(data)
    out: dict = {"count": len(notes)}
    for n in notes:
        node = out
        for part in PurePosixPath(n["path"]).parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("_notes", []).append({"title": n["title"], "path": n["path"], "summary": n["summary"]})
    return out


def get(name: str, data: Path | None = None) -> dict:
    """One note by relative path (.md optional), title or alias (case/accent-insensitive): {path, title, props, text}."""
    notes = load(data)
    key = fold(name.removesuffix(".md"))
    for n in notes:
        if key == fold(n["path"].removesuffix(".md")) or key in (fold(x) for x in _names(n)):
            return {"path": n["path"], "title": n["title"], "props": n["props"],
                    "text": (root(data) / n["path"]).read_text(encoding="utf-8")}
    titles = {fold(n["title"]): n["title"] for n in notes}
    near = difflib.get_close_matches(key, list(titles), n=3, cutoff=0)
    return {"error": f"Không có note '{name}'", "suggestions": [titles[t] for t in near]}


def add(note: str, text: str, section: str = "Câu hỏi học viên hay hỏi", data: Path | None = None) -> dict:
    """Append text at the end of '## section' of a note (section/note created when missing). note = title or relative path."""
    found = get(note, data)
    if "error" not in found:
        rel = found["path"]
    else:
        rel = note if note.endswith(".md") else note + ".md"
        p = PurePosixPath(rel)
        if p.is_absolute() or ".." in p.parts or "\\" in rel:
            return {"error": "đường dẫn phải nằm trong knowledge/"}
    path = root(data) / rel
    created = not path.exists()
    if created:
        props, body = {"title": PurePosixPath(rel).stem, "tags": [TAG]}, f"# {PurePosixPath(rel).stem}\n"
    else:
        props, body = split_note(path.read_text(encoding="utf-8"))
    body, text = body.rstrip(), text.strip()
    m = re.search(rf"^## +{re.escape(section)}\s*$", body, re.M)
    if m:
        nxt = re.search(r"^## ", body[m.end():], re.M)
        cut = m.end() + nxt.start() if nxt else len(body)
        body = body[:cut].rstrip() + f"\n\n{text}\n\n" + body[cut:].lstrip()
    else:
        body += f"\n\n## {section}\n\n{text}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(join_note(props, body), encoding="utf-8")
    return {"path": rel, "section": section, "created": created}
