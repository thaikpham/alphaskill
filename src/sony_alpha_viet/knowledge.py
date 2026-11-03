"""Knowledge management: markdown notes with YAML front matter, searchable, mirrored to Obsidian."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

from .core import nfc
from .paths import DATA


def _fold(text: str) -> str:
    """Normalize: NFC, lowercase, strip combining marks for accent-insensitive search."""
    t = nfc(text).lower()
    # Remove combining marks (diacritics) for accent-insensitive match
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return t


def load(data: Path | None = None) -> list[dict]:
    """Load all markdown notes under knowledge/.
    Returns [{path: rel posix, title, props, body, summary, sections: [{heading, text}]}]."""
    kb_dir = (data or DATA) / "knowledge"
    if not kb_dir.exists():
        return []

    notes = []
    for md_file in sorted(kb_dir.rglob("*.md")):
        rel_path = md_file.relative_to(kb_dir).as_posix()
        props, body = _read_note(md_file)
        title = props.get("title") or md_file.stem

        # Extract summary: first bold sentence or first paragraph, ≤200 chars
        summary = _extract_summary(body)

        # Extract sections: {heading, text} before first ## is the title section
        sections = _extract_sections(body, title)

        notes.append({
            "path": rel_path,
            "title": title,
            "props": props,
            "body": body,
            "summary": summary,
            "sections": sections
        })

    return notes


def search(query: str, limit: int = 6, data: Path | None = None) -> list[dict]:
    """Rank sections by relevance. Fold text for accent-free search.
    Returns [{note: path, title, section: heading, score, text}]."""
    notes = load(data)
    if not notes:
        return []

    query_tokens = query.split()
    query_fold = _fold(query)
    query_tokens_fold = [_fold(t) for t in query_tokens if len(t) >= 2]

    results = []
    for note in notes:
        for section in note["sections"]:
            heading = section["heading"]
            text = section["text"]
            text_fold = _fold(text)
            title_fold = _fold(note["title"])

            score = 0.0

            # 3x for exact phrase hits (either original or folded)
            if query.lower() in text.lower():
                score += 3.0
            if query_fold in text_fold:
                score += 3.0

            # Token overlap with IDF weighting
            if query_tokens_fold:
                # Count how many tokens appear in this section
                token_hits = sum(1 for t in query_tokens_fold if t in text_fold)
                if token_hits > 0:
                    # Simple IDF: sections with fewer unique tokens get higher weight
                    section_tokens = set(_fold(w) for w in re.findall(r"\w+", text) if len(w) >= 2)
                    idf = 1.0 / max(1, len(section_tokens)) if section_tokens else 1.0
                    score += token_hits * idf

            # 2x if query/tokens match title or aliases
            if query.lower() in note["title"].lower():
                score += 2.0
            if query_fold in title_fold:
                score += 2.0

            aliases = note["props"].get("aliases", [])
            for alias in aliases:
                if query.lower() in str(alias).lower():
                    score += 1.5
                if query_fold in _fold(str(alias)):
                    score += 1.5

            if score > 0:
                results.append({
                    "note": note["path"],
                    "title": note["title"],
                    "section": heading,
                    "score": round(score, 2),
                    "text": text[:1200]
                })

    # Sort by score desc, then by path/heading for deterministic tie-break
    results.sort(key=lambda x: (-x["score"], x["note"], x["section"]))
    return results[:limit]


def tree(data: Path | None = None) -> dict:
    """Return tree structure: {folder: {subfolder: ..., "_notes": [...]}, count: int}."""
    notes = load(data)
    root = {"count": len(notes)}
    tree_map = {}

    for note in notes:
        path_parts = note["path"].rstrip(".md").split("/")
        current = root

        # Navigate/create tree structure
        for i, part in enumerate(path_parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        # Add note to leaf folder's _notes
        if "_notes" not in current:
            current["_notes"] = []
        current["_notes"].append({
            "title": note["title"],
            "path": note["path"],
            "summary": note["summary"]
        })

    return root


def get(name: str, data: Path | None = None) -> dict:
    """Get by rel path (with/without .md) or title/alias (case/accent-insensitive).
    Returns {path, title, props, text} or {error, suggestions: [3 closest titles]}."""
    notes = load(data)
    if not notes:
        return {"error": "Không có kho kiến thức"}

    # Normalize lookup name
    name_fold = _fold(name.rstrip(".md"))
    name_lower = name.lower().rstrip(".md")

    # Try exact path match
    for note in notes:
        if name_lower == note["path"].lower().rstrip(".md"):
            return {"path": note["path"], "title": note["title"], "props": note["props"], "text": note["body"]}

    # Try title/alias match
    for note in notes:
        if name_fold == _fold(note["title"]):
            return {"path": note["path"], "title": note["title"], "props": note["props"], "text": note["body"]}

        for alias in note["props"].get("aliases", []):
            if name_fold == _fold(str(alias)):
                return {"path": note["path"], "title": note["title"], "props": note["props"], "text": note["body"]}

    # Not found: return suggestions (3 closest by fuzzy title match)
    titles = [n["title"] for n in notes]
    suggestions = sorted(
        titles,
        key=lambda t: _string_distance(_fold(t), name_fold)
    )[:3]

    return {"error": f"Không tìm thấy: {name}", "suggestions": suggestions}


def add(note: str, text: str, section: str = "Câu hỏi học viên hay hỏi", data: Path | None = None) -> dict:
    """Append text to a note's section. Create section/note if missing.
    Returns {path, section, created: bool}."""
    kb_dir = (data or DATA) / "knowledge"

    # Safety: refuse paths escaping knowledge/
    if ".." in note or note.startswith("/"):
        return {"error": "Đường dẫn không hợp lệ"}

    # Normalize note path
    note_path = note.rstrip(".md")
    if not note_path.endswith(".md"):
        note_path += ".md"

    full_path = kb_dir / note_path

    # Check if note exists
    created = False
    if full_path.exists():
        props, body = _read_note(full_path)
        title = props.get("title") or full_path.stem
    else:
        # Create new note
        full_path.parent.mkdir(parents=True, exist_ok=True)
        title = full_path.stem
        props = {"title": title, "tags": ["sony-alpha-viet/kien-thuc"]}
        body = f"# {title}"
        created = True

    # Find or create section
    section_pattern = f"## {re.escape(section)}"
    if re.search(f"^{section_pattern}$", body, re.MULTILINE):
        # Section exists: append to end of section
        # Find the end of this section (before next ##)
        pattern = f"(^## {re.escape(section)}.*?)(?:^##|\\Z)"
        match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
        if match:
            section_end = match.end(1)
            body = body[:section_end] + "\n\n" + text.strip() + body[section_end:]
    else:
        # Section missing: append at end
        body = body + "\n\n" + f"## {section}\n\n{text.strip()}"

    # Write note
    _write_note(full_path, props, body)
    return {"path": note_path, "section": section, "created": created}


# ---- Helpers ----

def _read_note(path: Path) -> tuple[dict, str]:
    """Read YAML frontmatter and body."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    try:
        props = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        props = {}
    return (props if isinstance(props, dict) else {}), text[m.end():]


def _write_note(path: Path, props: dict, body: str):
    """Write YAML frontmatter and body."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = yaml.safe_dump(props, allow_unicode=True, sort_keys=False, width=10**6).strip()
    path.write_text(f"---\n{fm}\n---\n\n{body.strip()}\n", encoding="utf-8")


def _extract_summary(body: str) -> str:
    """Extract first bold sentence or first paragraph, ≤200 chars."""
    # Look for **text** (bold)
    m = re.search(r"\*\*(.*?)\*\*", body)
    if m:
        summary = m.group(1)
        if len(summary) <= 200:
            return summary
        return summary[:197] + "…"

    # First paragraph
    para = body.split("\n\n")[0].replace("#", "").strip()
    if len(para) <= 200:
        return para
    return para[:197] + "…"


def _extract_sections(body: str, title: str) -> list[dict]:
    """Extract sections from markdown body.
    Text before first ## becomes a section with heading = title."""
    sections = []

    # First section (before any ##)
    first_section = re.split(r"^## ", body, 1, re.MULTILINE)[0].replace(f"# {title}", "").strip()
    if first_section:
        sections.append({"heading": title, "text": first_section})

    # Named sections
    for m in re.finditer(r"^## (.+?)$\n(.*?)(?=^##|\Z)", body, re.MULTILINE | re.DOTALL):
        heading = m.group(1).strip()
        text = m.group(2).strip()
        if text:
            sections.append({"heading": heading, "text": text})

    return sections


def _string_distance(a: str, b: str) -> int:
    """Simple edit distance for fuzzy matching."""
    from difflib import SequenceMatcher
    return 1 - SequenceMatcher(None, a, b).ratio()


def sha1_note(text: str) -> str:
    """SHA1 hash of note text for detecting edits."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()
