"""Official Sony Vietnamese documents (Startup Guides, Help Guide PDFs) and English Help Guides as a searchable reference corpus.

Ingested text lives in the private data dir (DATA/docs/) — Sony's documents never go into the public repo.
Used to answer "how does Sony Vietnam officially phrase this?" and to check the glossary against real usage.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import time
import unicodedata
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

from . import core

# ---------------- VNI-Windows → Unicode (older Sony VN PDFs, e.g. ILCE-6400) ----------------
_VNI = {}
for base, table in {
    "a": {"â": "â", "ê": "ă", "ù": "á", "ø": "à", "û": "ả", "õ": "ã", "ï": "ạ", "á": "ấ", "à": "ầ", "å": "ẩ", "ã": "ẫ", "ä": "ậ",
          "é": "ắ", "è": "ằ", "ú": "ẳ", "ü": "ẵ", "ë": "ặ"},
    "e": {"â": "ê", "ù": "é", "ø": "è", "û": "ẻ", "õ": "ẽ", "ï": "ẹ", "á": "ế", "à": "ề", "å": "ể", "ã": "ễ", "ä": "ệ"},
    "o": {"â": "ô", "ù": "ó", "ø": "ò", "û": "ỏ", "õ": "õ", "ï": "ọ", "á": "ố", "à": "ồ", "å": "ổ", "ã": "ỗ", "ä": "ộ"},
    "ô": {"": "ơ", "ù": "ớ", "ø": "ờ", "û": "ở", "õ": "ỡ", "ï": "ợ"},
    "u": {"ù": "ú", "ø": "ù", "û": "ủ", "õ": "ũ", "ï": "ụ"},
    "ö": {"": "ư", "ù": "ứ", "ø": "ừ", "û": "ử", "õ": "ữ", "ï": "ự"},
    "y": {"ù": "ý", "ø": "ỳ", "û": "ỷ", "õ": "ỹ"},
}.items():
    for mod, out in table.items():
        _VNI[base + mod] = out
        _VNI[base.upper() + mod] = out.upper()
        _VNI[base.upper() + mod.upper()] = out.upper()
_VNI.update({"í": "í", "ì": "ì", "æ": "ỉ", "ó": "ĩ", "ò": "ị", "î": "ỵ", "ñ": "đ", "Ñ": "Đ",
             "Í": "Í", "Ì": "Ì", "Æ": "Ỉ", "Ó": "Ĩ", "Ò": "Ị", "Î": "Ỵ"})
_VNI_RX = re.compile("|".join(sorted(map(re.escape, _VNI), key=len, reverse=True)))
_VI_UNI = re.compile("[ạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹđươĐƯƠ]")


def looks_vni(text: str) -> bool:
    """VNI text has many 'ñ', 'ö', 'ô+tone' sequences and almost no real Vietnamese Unicode letters."""
    vni = len(re.findall(r"ñ|ö|[aeo][âùøûõïáàåãäéèúüë]|ô[ùøûõï]", text))
    return vni > 20 and vni > 5 * len(_VI_UNI.findall(text))


def vni_to_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", _VNI_RX.sub(lambda m: _VNI[m.group(0)], text))


# ---------------- extraction ----------------
def _pdf_pages(path: Path) -> list[str]:
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
    n = int(re.search(r"Pages:\s+(\d+)", info).group(1)) if "Pages:" in info else 1
    pages = []
    for i in range(1, n + 1):
        out = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), str(path), "-"], capture_output=True, text=True).stdout
        pages.append(re.sub(r"\n{3,}", "\n\n", out).strip())
    return pages


def _model(name: str, text: str) -> str:
    m = re.search(r"\b(ILCE-[0-9A-Z]+|ZV-E\d+M?\d?)\b", text)
    if m:
        return m.group(1)
    n = name.upper().replace(" ", "")
    n = re.sub(r"^A(\d)", r"ILCE-\1", n)
    return n


def _docx_links(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as z:
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
        doc = z.read("word/document.xml").decode("utf-8")
    targets = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(http[^"]+)"', rels))
    targets.update({k: v for v, k in re.findall(r'Target="(http[^"]+)"[^>]*Id="(rId\d+)"', rels)})
    out = []
    for rid, inner in re.findall(r'<w:hyperlink[^>]*r:id="(rId\d+)"[^>]*>(.*?)</w:hyperlink>', doc, re.S):
        title = re.sub(r"<[^>]+>", "", inner).strip()
        if rid in targets:
            out.append({"title": title, "url": targets[rid]})
    return out


def ingest(folder: str, data: Path | None = None) -> dict:
    """Read every PDF/DOCX in folder into DATA/docs/. Identical files are stored once. Re-running replaces the corpus.
    Preserves entries with "source_url" from previous helpguide ingests."""
    data = data or core.DATA
    out_dir = data / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Path(folder).expanduser()

    # Load existing index to preserve helpguide entries
    existing_by_id = {}
    if (out_dir / "index.json").exists():
        try:
            existing_idx = json.loads((out_dir / "index.json").read_text(encoding="utf-8"))
            existing_by_id = {d["id"]: d for d in existing_idx.get("docs", []) if d.get("source_url")}
        except Exception:
            pass

    index, seen, links, dupes = [], {}, [], []
    for f in sorted(src.rglob("*")):
        if f.suffix.lower() == ".docx":
            links += _docx_links(f)
            continue
        if f.suffix.lower() != ".pdf":
            continue
        md5 = hashlib.md5(f.read_bytes()).hexdigest()
        if md5 in seen:
            dupes.append({"file": f.name, "same_as": seen[md5]})
            continue
        seen[md5] = f.name
        pages = _pdf_pages(f)
        raw = "\n".join(pages)
        enc = "vni" if looks_vni(raw) else "unicode"
        if enc == "vni":
            pages = [vni_to_unicode(p) for p in pages]
        text = "\n".join(pages)
        code = re.search(r"\b([A-Z0-9]-\d{3}-\d{3}-\d{2}\(\d\)|\d-\d{3}-\d{3}-\d{2}\(\d\))", text)
        doc_id = re.sub(r"[^a-z0-9]+", "-", f.stem.lower()).strip("-")
        meta = {"id": doc_id, "file": f.name, "md5": md5, "model": _model(f.stem, text), "code": code.group(1) if code else "",
                "kind": "Hướng dẫn khởi động" if "Khởi động" in text or len(pages) <= 4 else "Tài liệu", "pages": len(pages),
                "encoding": enc, "chars": len(text), "lang": "vi"}
        body = "\n\n".join(f"## Trang {i}\n\n{p}" for i, p in enumerate(pages, 1))
        (out_dir / f"{doc_id}.md").write_text(body + "\n", encoding="utf-8")
        index.append(meta)

    # Add back preserved helpguide entries
    index.extend(existing_by_id.values())

    (out_dir / "index.json").write_text(json.dumps({"source": str(src), "docs": index, "links": links, "duplicates": dupes},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    return {"docs": len(index), "pages": sum(d["pages"] for d in index), "vni_converted": [d["file"] for d in index if d.get("encoding") == "vni"],
            "duplicates": dupes, "links": len(links), "stored_in": str(out_dir)}


def _strip_html(html_text: str) -> str:
    """Strip HTML tags, unescape entities, preserve [Menu items] and structure."""
    # Remove script and style tags
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.S | re.I)
    # Preserve [Menu] brackets before converting
    text = text.replace("[", "\x00[").replace("]", "]\x00")
    # Replace common block elements with newlines
    text = re.sub(r"</?(p|div|section|article|h[1-6]|li|dt|dd)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<br\s*/?>\s*", "\n", text, flags=re.I)
    # Remove all other tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Restore [Menu] brackets
    text = text.replace("\x00[", "[").replace("]\x00", "]")
    # Unescape HTML entities
    text = html.unescape(text)
    # Collapse multiple spaces and normalize newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\n\n+", "\n\n", text)
    return text.strip()


def _fetch_url(url: str, timeout: int = 5) -> str:
    """Fetch URL with retry once on failure, small timeout."""
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Sony Alpha Vietnamese skill"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError):
            if attempt == 1:
                raise
            time.sleep(0.5)


def _extract_help_links(index_html: str) -> list[str]:
    """Extract unique contents/*.html links from index in document order (deduplicated, order preserved)."""
    links = []
    seen = set()
    for match in re.finditer(r'href="([^"]*contents[/\\][^"]*\.html)"', index_html, re.I):
        url = match.group(1).replace("\\", "/")  # normalize backslashes
        if url not in seen:
            links.append(url)
            seen.add(url)
    return links


def ingest_helpguide(url: str, data: Path | None = None) -> dict:
    """Fetch Sony Help Guide (HTML, English) from index URL, extract all content pages, convert to markdown with page format.
    Merges into DATA/docs/ without overwriting other docs. Pages stay in private DATA, never in public repo."""
    data = data or core.DATA
    out_dir = data / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    lang = "en"

    # Fetch index page first
    try:
        index_html = _fetch_url(url)
    except (urllib.error.URLError, TimeoutError) as e:
        return {"ok": False, "error": f"Failed to fetch index: {e}"}

    # Extract model: first ILCE-/ZV- match in HTML, fallback to URL
    model = re.search(r'\b(ILCE-[0-9A-Z]+|ZV-[0-9A-Z]+)\b', index_html)
    if not model:
        model_match = re.search(r"/ilc/(\d+)/", url, re.I)
        model = f"ILCE-{model_match.group(1)}" if model_match else "UNKNOWN"
    else:
        model = model.group(1)

    # Generate doc_id from model and lang
    doc_id = f"helpguide-{model.lower()}-{lang}"

    # Extract content links
    links = _extract_help_links(index_html)
    if not links:
        return {"ok": False, "error": "No content pages found in index"}

    # Fetch and process each page
    pages, chars = [], 0
    base_url = url.rsplit("/", 1)[0]  # directory of index.html

    for link in links:
        # Resolve relative URL
        if not link.startswith("http"):
            link = base_url + "/" + link if not link.startswith("/") else base_url.split("//", 1)[0] + "//" + base_url.split("//", 1)[1].split("/", 1)[0] + link

        try:
            page_html = _fetch_url(link, timeout=3)
            # Extract <main> content and title
            main_match = re.search(r"<main[^>]*>(.*?)</main>", page_html, re.S | re.I)
            if main_match:
                text = _strip_html(main_match.group(1))
                if text:
                    pages.append(text)
                    chars += len(text)
        except (urllib.error.URLError, TimeoutError):
            # Skip pages that fail to fetch
            continue

    if not pages:
        return {"ok": False, "error": "No pages could be fetched"}

    # Write markdown file
    body = "\n\n".join(f"## Trang {i}\n\n{p}" for i, p in enumerate(pages, 1))
    (out_dir / f"{doc_id}.md").write_text(body + "\n", encoding="utf-8")

    # Create or merge index.json
    try:
        existing_idx = json.loads((out_dir / "index.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        existing_idx = {"source": url, "docs": [], "links": [], "duplicates": []}

    # Replace entry with same id if exists
    existing_idx["docs"] = [d for d in existing_idx.get("docs", []) if d.get("id") != doc_id]

    meta = {
        "id": doc_id, "model": model, "kind": "Help Guide (EN)", "lang": lang, "pages": len(pages),
        "chars": chars, "source_url": url
    }
    existing_idx["docs"].append(meta)

    (out_dir / "index.json").write_text(json.dumps(existing_idx, ensure_ascii=False, indent=1), encoding="utf-8")

    return {
        "ok": True, "doc_id": doc_id, "model": model, "pages": len(pages), "chars": chars,
        "url": url, "stored_in": str(out_dir / f"{doc_id}.md")
    }


# ---------------- corpus access ----------------
def load(data: Path | None = None) -> dict:
    d = (data or core.DATA) / "docs"
    if not (d / "index.json").exists():
        return {"docs": [], "links": [], "texts": {}}
    idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
    idx["texts"] = {m["id"]: (d / f"{m['id']}.md").read_text(encoding="utf-8") for m in idx["docs"] if (d / f"{m['id']}.md").exists()}
    return idx


def _fold(s: str) -> str:
    return unicodedata.normalize("NFC", s).lower()


def search(query: str, limit: int = 10, data: Path | None = None) -> list[dict]:
    """Official-doc passages containing the query as a phrase (case-insensitive; also across a line break), with model, page, and lang."""
    corpus = load(data)
    q = re.sub(r"\s+", " ", _fold(query)).strip()
    meta = {m["id"]: m for m in corpus["docs"]}
    hits, seen = [], set()
    for doc_id, text in corpus["texts"].items():
        for page_no, page in re.findall(r"## Trang (\d+)\n(.*?)(?=\n## Trang |\Z)", text, re.S):
            flat = re.sub(r"\s+", " ", page)
            for m in re.finditer(re.escape(q), _fold(flat)):
                a, b = max(0, m.start() - 120), min(len(flat), m.end() + 120)
                snippet = ("…" if a else "") + flat[a:b].strip() + ("…" if b < len(flat) else "")
                key = (meta[doc_id]["model"], flat[m.start():m.end() + 60])
                if key in seen:
                    continue
                seen.add(key)
                doc_meta = meta[doc_id]
                hits.append({"model": doc_meta["model"], "doc": doc_meta.get("file", doc_meta.get("id")), "page": int(page_no),
                             "lang": doc_meta.get("lang", "vi"), "match": flat[m.start():m.end()], "text": snippet})
    return hits[:limit]


def _per_model(phrase: str, data: Path | None = None) -> dict:
    c = Counter(h["model"] for h in search(phrase, 10_000, data))
    return dict(sorted(c.items()))


def term_report(store: core.Store, data: Path | None = None) -> dict:
    """Glossary vs. official Sony VN usage: terms Sony uses, banned forms Sony uses, English words Sony keeps.
    Skips EN-language docs as they don't reflect Vietnamese usage."""
    corpus = load(data)
    # Skip EN docs: only use Vietnamese docs for term report
    meta_by_id = {m["id"]: m for m in corpus["docs"]}
    vi_texts = [t for doc_id, t in corpus["texts"].items() if meta_by_id.get(doc_id, {}).get("lang", "vi") == "vi"]
    vi_docs = len(vi_texts)
    text = "\n".join(vi_texts) if vi_texts else ""
    low = _fold(text)
    used, unused = [], []
    for g in store.glossary:
        if not g.get("locked") or len(g["vi"]) < 4:  # 'cao', 'thấp'… are too generic to count as evidence
            continue
        n = len(re.findall(r"(?<!\w)" + re.escape(_fold(g["vi"])) + r"(?!\w)", low))
        (used if n else unused).append({"en": g["en"], "vi": g["vi"], "count": n})
    banned = []
    for b in store.rules.get("banned", []):
        found = sorted({m.group(0).lower() for m in re.finditer(b["pattern"], text)})
        for f in found:
            ex = search(f, 3, data)
            # Filter search results to only include VI docs
            ex = [h for h in ex if meta_by_id.get(h.get("doc", "").replace(".md", ""), {}).get("lang", "vi") == "vi"]
            banned.append({"pattern": b["pattern"], "why": b["why"], "sony_uses": f, "by_model": _per_model(f, data),
                           "examples": [f"{h['model']} tr.{h['page']}: {h['text']}" for h in ex]})
    # Latin words Sony keeps inside Vietnamese sentences (not URLs, [English menu names], trademark/legal lines)
    latin, models_of = Counter(), {}
    for doc_id, body in corpus["texts"].items():
        # Only check VI docs
        if meta_by_id.get(doc_id, {}).get("lang") == "en":
            continue
        for line in body.split("\n"):
            if not core.VI_CHARS.search(line) or re.search(r"https?://|www\.|®|™|Inc\.|Corporation|thương hiệu|nhãn hiệu|iPhone|iPad|Apple|Android|Made for|San Diego", line):
                continue
            for w in re.findall(r"(?<![\w\-/.])[A-Za-z][A-Za-z+]{2,}(?![\w\-/.])", re.sub(r"\[[^\]]*\]", " ", line)):
                if core.VI_CHARS.search(w) or w.lower() in core.VI_ASCII:
                    continue
                if not (w[0].isupper() or re.search(r"[fjwz]", w) or len(w) >= 6):  # unaccented Vietnamese words: vai, xong…
                    continue
                latin[w] += 1
                models_of.setdefault(w, set()).add(doc_id)
    keep_terms = {k["term"].lower() for k in store.keep}
    kept = [{"word": w, "count": n, "models": len(models_of[w]), "known": w in store.allow or w.lower() in keep_terms or w.isupper()}
            for w, n in latin.most_common() if n >= 2 and len(models_of[w]) >= 2]
    return {"docs": vi_docs, "locked_terms_used_by_sony": sorted(used, key=lambda x: -x["count"]),
            "locked_terms_not_seen": unused, "banned_forms_sony_uses": banned,
            "english_kept_by_sony": [k for k in kept if not k["known"]][:40]}
