"""alphaskill Markdown <-> Alpha ColorLab `Article` (github.com/thaikpham/alphacolorlab.com).

The site's contract lives in `src/lib/lab/types.ts` (closed 10-block union) and its publish
gate in `parse.ts` (`validateForPublish`) + `packs/check.ts`. `check()` here ports that gate
for early feedback; the site's own `packs.test.ts` stays the authority (`write_pack` runs it).

Markdown accepted (see skills/sony-alpha-viet/references/colorlab-vi.md):
  frontmatter  slug, title|meta_title, dek|meta_description, read, kind, topic, level, archetype,
               section, order, author, reviewed, updated|checked, related ["recipe:PP-001"],
               prerequisites, concepts
  # H1         title (the italic byline under it is dropped)
  **TL;DR:**   + three `- ` lines (or three sentences)        -> tldr
  ## / ###     -> h ("Câu hỏi thường gặp" itself is dropped; its ### questions become h + p)
  paragraph    -> p (inline Markdown stripped; consecutive paragraphs merge: the site refuses p after p)
  3-col table  + `*caption*` line                             -> table
  > **Nếu …:** text                                          -> callout
  > MENU → … (old)  /  > MENU → … (new)                       -> menu
  > **So sánh:** before | after  /  > caption                 -> compare
  **Label:** + `- [ ]` lines                                  -> checklist
  ![alt](asset:<uuid>) + `*caption*`                          -> figure
  bare YouTube/Vimeo URL + `*caption*`                         -> embed
  ## Nguồn tham khảo  `- [title](url)` / `- title — url`      -> meta.sources
"""
from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from typing import Any

EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF⌀-⏿☀-➿⬀-⯿]")
PLACEHOLDER = "[CẦN BỔ SUNG"
UNVERIFIED = re.compile(r"\[cần xác minh", re.I)
FAQ = {"câu hỏi thường gặp", "faq", "hỏi đáp"}
SOURCES = {"nguồn tham khảo", "nguồn", "sources", "tham khảo"}
VIDEO = re.compile(r"^<?https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|vimeo\.com/)([\w-]+)\S*?>?$")
TOPICS = {"setup", "color", "af", "exposure", "composition", "lens", "body", "video", "audio", "post", "gear", "firmware"}
LEVELS = {"newbie", "mid", "pro"}
ARCHETYPES = {"setup-guide", "versus", "technique", "explainer", "fix", "gear", "recipe"}
SECTIONS = {"fundamentals", "sony-color", "workflows"}
RESERVED_IDS = {"setup", "admin", "new", "glossary", "search"}


def slugify(title: str) -> str:
    """Port of `slugify` in parse.ts."""
    s = re.sub("[̀-ͯ]", "", unicodedata.normalize("NFD", title)).replace("đ", "d").replace("Đ", "D").lower()
    return re.sub(r"-+$", "", re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", s))[:60])


def plain(md: str) -> str:
    md = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"(\*\*|__)(.+?)\1", r"\2", md)
    md = re.sub(r"(?<![\w*])[*_](\S(?:.*?\S)?)[*_](?![\w*])", r"\1", md)
    return unicodedata.normalize("NFC", re.sub(r"`([^`]*)`", r"\1", md).strip())


def _iso(v: Any) -> str | None:
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%Y-%m-%d")
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(v or "").strip())
    if m:
        return f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
    return str(v).strip() if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v or "").strip()) else None


def _frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"﻿?---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    import yaml
    try:
        fm = yaml.safe_load(m[1]) or {}
    except yaml.YAMLError:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), text[m.end():]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.?…])\s+(?=[A-ZÀ-Ỹ\d])", text) if s.strip()]


def _source(line: str, checked: str | None) -> dict | None:
    line = re.sub(r"^\s*[-*+]\s+|^\s*\d+\.\s+", "", line).strip()
    date = re.search(r"\s*[·—–(]\s*(?:kiểm\s*)?(\d{4}-\d{2}-\d{2})\)?\s*$", line)
    if date:
        checked, line = date[1], line[:date.start()]
    m = re.fullmatch(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", line) or \
        re.fullmatch(r"\[?(.+?)\s*[—:–-]\s*<?(https?://[^\s>\]]+)>?\]?", line)
    if not m:
        return None
    host = re.sub(r"^https?://", "", m[2]).split("/")[0]
    src = {"url": m[2], "title": plain(m[1]).strip(" —-"),
           "publisher": "Sony" if re.search(r"(^|\.)sony[\w-]*\.", host) else "other"}
    if checked:
        src["checkedAt"] = checked
    return src


def md_to_article(text: str, **overrides) -> dict[str, Any]:
    """Markdown -> {"article": Article, "problems": [...], "notes": [...]}."""
    fm, body = _frontmatter(unicodedata.normalize("NFC", text))
    fm.update({k: v for k, v in overrides.items() if v not in ("", None)})
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    checked = _iso(fm.get("checked") or fm.get("updated"))
    blocks: list[dict] = []
    sources: list[dict] = []
    notes: list[str] = []
    title = plain(str(fm.get("title") or ""))
    lines = body.split("\n")
    i, in_sources, after_h1 = 0, False, False

    def caption_at(j: int) -> tuple[str, int]:
        while j < len(lines) and not lines[j].strip():
            j += 1
        s = lines[j].strip() if j < len(lines) else ""
        return (plain(s), j + 1) if re.fullmatch(r"[*_][^*_].*[*_]", s) else ("", j)

    def add_p(t: str) -> None:
        if blocks and blocks[-1]["t"] == "p":
            blocks[-1]["text"] += " " + t
            notes.append("merged consecutive paragraphs (site refuses p after p)")
        else:
            blocks.append({"t": "p", "text": t})

    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if m := re.match(r"(#{1,6})\s+(.*)", s):
            text_h, level = plain(m[2]), len(m[1])
            i += 1
            if level == 1:
                title = title or text_h
                after_h1 = True
                continue
            in_sources = text_h.lower().rstrip(":") in SOURCES
            if not in_sources and text_h.lower().rstrip(":") not in FAQ:
                blocks.append({"t": "h", "text": text_h})
            continue
        if after_h1 and re.fullmatch(r"[*_](?![*_]).+(?<![*_])[*_]", s):  # byline
            after_h1 = False
            i += 1
            continue
        after_h1 = False
        if in_sources:
            if src := _source(s, checked):
                sources.append(src)
            i += 1
            continue
        if m := re.match(r"\*\*(TL;DR|Tóm tắt|Trả lời nhanh)\s*:?\*\*\s*:?\s*(.*)", s, re.I):
            items, i = ([plain(m[2])] if m[2] else []), i + 1
            while i < len(lines) and re.match(r"\s*[-*+]\s+", lines[i]):
                items.append(plain(re.sub(r"^\s*[-*+]\s+", "", lines[i])))
                i += 1
            if len(items) == 1:
                items = _sentences(items[0])
            blocks.append({"t": "tldr", "items": items})
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [plain(c) for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells):
                    rows.append(cells)
                i += 1
            cap, i = caption_at(i)
            blocks.append({"t": "table", "head": rows[0] if rows else [], "rows": rows[1:], "caption": cap})
            continue
        if s.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            quote = [q for q in quote if q]
            paths = [re.sub(r"^[^:]*:\s*(?=MENU)", "", q) for q in quote]
            if len(paths) == 2 and all(p.startswith("MENU") for p in paths):
                blocks.append({"t": "menu", "old": plain(paths[0]), "new": plain(paths[1])})
            elif quote and (m := re.match(r"\*\*So sánh\s*:?\*\*\s*:?\s*(.+?)\s*\|\s*(.+)", quote[0], re.I)):
                blocks.append({"t": "compare", "beforeLabel": plain(m[1]), "afterLabel": plain(m[2]),
                               "caption": plain(" ".join(quote[1:]))})
            elif quote and (m := re.match(r"\*\*(.+?)\s*:?\*\*\s*:?\s*(.*)", quote[0])):
                blocks.append({"t": "callout", "label": plain(m[1]).rstrip(":"), "text": plain(" ".join([m[2], *quote[1:]]))})
            else:
                add_p(plain(" ".join(quote)))
            continue
        if m := re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]*)\)", s):
            cap, i = caption_at(i + 1)
            fig = {"t": "figure", "caption": cap}
            if m[1]:
                fig["alt"] = plain(m[1])
            if m[2].startswith("asset:") and m[2][6:]:
                fig["assetId"] = m[2][6:]
            else:
                notes.append(f"figure '{m[1] or m[2]}' needs an upload from the page's Sửa")
            blocks.append(fig)
            continue
        if m := VIDEO.match(s):
            cap, i = caption_at(i + 1)
            blocks.append({"t": "embed", "provider": "vimeo" if "vimeo" in s else "youtube", "id": m[1], "caption": cap})
            continue
        if re.match(r"[-*+]\s+\[[ xX]\]\s+", s):
            items = []
            while i < len(lines) and re.match(r"\s*[-*+]\s+\[[ xX]\]\s+", lines[i]):
                items.append(plain(re.sub(r"^\s*[-*+]\s+\[[ xX]\]\s+", "", lines[i])))
                i += 1
            label = ""
            if blocks and blocks[-1]["t"] == "p" and blocks[-1].get("_label"):
                label = blocks.pop()["text"]
            blocks.append({"t": "checklist", "label": label, "items": items})
            continue
        if re.match(r"([-*+]|\d+[.)])\s+", s):
            items = []
            while i < len(lines) and re.match(r"\s*([-*+]|\d+[.)])\s+", lines[i]):
                items.append(plain(re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", lines[i])).rstrip(".;"))
                i += 1
            add_p("; ".join(items) + ".")
            notes.append("a list became one paragraph (the site has no list block): rewrite it as prose")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"\s*(#|>|\||[-*+]\s|\d+[.)]\s|!\[)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        joined = " ".join(para)
        if m := re.fullmatch(r"\*\*(.+?):?\*\*:?", joined):  # a bold label line before a checklist
            blocks.append({"t": "p", "text": plain(m[1]).rstrip(":"), "_label": True})
        else:
            add_p(plain(joined))

    for b in blocks:
        b.pop("_label", None)

    def lst(key: str) -> list:
        v = fm.get(key) or []
        return [str(x) for x in (v if isinstance(v, list) else [v])]

    related = [{"kind": k, "id": v} for k, _, v in (r.partition(":") for r in lst("related")) if v]
    order = fm.get("order")
    article = {
        "id": slugify(str(fm.get("slug") or title)),
        "kind": str(fm.get("kind") or "article"),
        "topic": str(fm.get("topic") or ""),
        "level": str(fm.get("level") or ""),
        "archetype": str(fm.get("archetype") or ""),
        "read": str(fm.get("read") or ""),
        "title": title,
        "dek": plain(str(fm.get("dek") or fm.get("meta_description") or "")),
        "blocks": blocks,
        "meta": {
            "related": related,
            "prerequisites": lst("prerequisites"),
            "concepts": lst("concepts"),
            "sources": fm["sources"] if isinstance(fm.get("sources"), list) else sources,
            "authorName": str(fm["author"]) if fm.get("author") else None,
            "reviewedAt": _iso(fm.get("reviewed")),
            "section": fm.get("section") or None,
            "order": int(order) if str(order or "").isdigit() else None,
        },
    }
    return {"article": article, "problems": check(article, unverified_text=body),
            "notes": sorted(set(notes))}


def _precis(section: list[dict]) -> str:
    for b in section:
        if b["t"] == "p":
            return b["text"]
    for b in section:
        if b["t"] == "callout":
            return b["text"]
        if b["t"] in ("figure", "table", "embed"):
            return b.get("caption", "")
    return ""


def check(article: dict, today: str | None = None, unverified_text: str = "") -> list[str]:
    """Port of `validateForPublish` + the pack gate's own codes, plus field/shape checks the
    TypeScript compiler would raise. Same codes as the site so messages line up."""
    today = today or dt.date.today().isoformat()
    a, meta, blocks = article, article["meta"], article["blocks"]
    types = [b["t"] for b in blocks]
    out: list[str] = []
    if not a["id"] or a["id"] in RESERVED_IDS:
        out.append("badId")
    if a["kind"] not in ("article", "knowledge"):
        out.append("badKind")
    if a["topic"] not in TOPICS:
        out.append("badTopic")
    if a["level"] not in LEVELS:
        out.append("badLevel")
    if a["archetype"] not in ARCHETYPES:
        out.append("badArchetype")
    if not a["title"].strip():
        out.append("emptyTitle")
    for b in blocks:
        if b["t"] == "tldr" and len(b["items"]) != 3:
            out.append("tldrItems")
        if b["t"] == "table" and (len(b["head"]) != 3 or any(len(r) != 3 for r in b["rows"])):
            out.append("tableColumns")
        if b["t"] == "table" and not b["caption"]:
            out.append("tableCaption")
        if b["t"] == "checklist" and not b["label"]:
            out.append("checklistLabel")
    if a["kind"] == "knowledge":
        if meta["section"] not in SECTIONS:
            out.append("knowledgeNeedsSection")
        if len(blocks) < 3:
            out.append("knowledgeTooShort")
        if len(blocks) > 32:
            out.append("knowledgeTooLong")
        if "h" not in types:
            out.append("knowledgeNeedsHeading")
        if len(a["dek"]) > 220:
            out.append("dekTooLong")
        if not meta["sources"]:
            out.append("knowledgeNeedsSource")
    else:
        if len(blocks) < 8:
            out.append("tooFewBlocks")
        if len(blocks) > 16:
            out.append("tooManyBlocks")
        if len(a["dek"]) > 220:
            out.append("dekTooLong")
        if not a["dek"].strip():
            out.append("emptyDek")
        if not a["read"].strip():
            out.append("emptyRead")
        if types[:1] != ["tldr"]:
            out.append("mustOpenWithTldr")
        if types[1:2] != ["p"]:
            out.append("tldrNeedsContext")
        if "h" not in types:
            out.append("needsHeading")
        elif types.index("h") <= 1:
            out.append("headingTooEarly")
        heads = [n for n, t in enumerate(types) if t == "h"]
        if any(not _precis(blocks[n + 1:(heads + [len(blocks)])[k + 1]]) for k, n in enumerate(heads)):
            out.append("sectionNeedsSummary")
        if types[-1:] not in (["checklist"], ["figure"]):
            out.append("mustCloseWithChecklistOrFigure")
        if any(t != "menu" and t == types[n - 1] for n, t in enumerate(types) if n):
            out.append("repeatedBlock")
    # houseRules
    if any(b["t"] == "menu" and not all(p.startswith("MENU") and " → " in p for p in (b["old"], b["new"])) for b in blocks):
        out.append("menuSeparator")
    if any(b["t"] == "table" and not 3 <= len(b["rows"]) <= 6 for b in blocks):
        out.append("tableRows")
    if any(b["t"] == "checklist" and not 3 <= len(b["items"]) <= 6 for b in blocks):
        out.append("checklistItems")
    bad_label = re.compile(r"(trước|sau|before|after)", re.I)
    if any(b["t"] == "compare" and (bad_label.fullmatch(b["beforeLabel"]) or bad_label.fullmatch(b["afterLabel"])) for b in blocks):
        out.append("compareLabels")
    if any(b["t"] == "callout" and re.fullmatch(r"(lưu ý|chú ý|note)", b["label"].strip(), re.I) for b in blocks):
        out.append("calloutLabel")
    prose = json.dumps([a["title"], a["dek"], a["read"], blocks], ensure_ascii=False)
    if EMOJI_RE.search(prose):
        out.append("emoji")
    if "!" in prose:
        out.append("exclamation")
    if PLACEHOLDER in prose:
        out.append("placeholder")
    if (meta["reviewedAt"] or "") > today or any((s.get("checkedAt") or "") > today for s in meta["sources"]):
        out.append("dateInFuture")
    if a["id"] in meta["prerequisites"] or any(r["kind"] in ("article", "knowledge") and r["id"] == a["id"] for r in meta["related"]):
        out.append("selfReference")
    # packProblems
    if not meta["sources"]:
        out.append("noSource")
    if any(not s.get("checkedAt") for s in meta["sources"]):
        out.append("sourceNeedsDate")
    if "figure" in types:
        out.append("figureNeedsUpload")
    # alphaskill: an unverified claim never ships to the site
    if UNVERIFIED.search(unverified_text or prose):
        out.append("unverified")
    return sorted(set(out))


def article_to_md(article: dict) -> str:
    """Article -> alphaskill Markdown (pull a site page into Obsidian, edit, push back)."""
    a, meta = article, article["meta"]
    fm = {"slug": a["id"], "title": a["title"], "dek": a["dek"], "read": a["read"], "kind": a["kind"],
          "topic": a["topic"], "level": a["level"], "archetype": a["archetype"]}
    if meta.get("section"):
        fm["section"] = meta["section"]
    if meta.get("order") is not None:
        fm["order"] = meta["order"]
    if meta.get("authorName"):
        fm["author"] = meta["authorName"]
    if meta.get("reviewedAt"):
        fm["reviewed"] = meta["reviewedAt"]
    dates = sorted({s["checkedAt"] for s in meta.get("sources", []) if s.get("checkedAt")})
    if dates:
        fm["checked"] = dates[-1]
    for key in ("prerequisites", "concepts"):
        if meta.get(key):
            fm[key] = list(meta[key])
    if meta.get("related"):
        fm["related"] = [f"{r['kind']}:{r['id']}" for r in meta["related"]]
    srcs = list(meta.get("sources", []))
    rich = any(set(x) - {"url", "title", "publisher", "checkedAt"} or x.get("publisher") != _source(
        f"- [{x['title']}]({x['url']})", None)["publisher"] for x in srcs)
    if rich:  # fields the Markdown line cannot carry: keep them whole
        fm["sources"], srcs = srcs, []
    import yaml
    out = ["---", yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip(), "---", "", f"# {a['title']}", ""]
    for b in a["blocks"]:
        t = b["t"]
        if t == "tldr":
            out += ["**TL;DR:**", *[f"- {x}" for x in b["items"]]]
        elif t == "h":
            out.append(f"## {b['text']}")
        elif t == "p":
            out.append(b["text"])
        elif t == "menu":
            out += [f"> {b['old']}", f"> {b['new']}"]
        elif t == "table":
            out += ["| " + " | ".join(b["head"]) + " |", "|---|---|---|",
                    *["| " + " | ".join(r) + " |" for r in b["rows"]], "", f"*{b['caption']}*"]
        elif t == "callout":
            out.append(f"> **{b['label']}:** {b['text']}")
        elif t == "compare":
            out += [f"> **So sánh:** {b['beforeLabel']} | {b['afterLabel']}", f"> {b['caption']}"]
        elif t == "checklist":
            out += [f"**{b['label']}:**", "", *[f"- [ ] {x}" for x in b["items"]]]
        elif t == "figure":
            out += [f"![{b.get('alt', '')}](asset:{b.get('assetId', '')})", "", f"*{b['caption']}*"]
        elif t == "embed":
            url = f"https://vimeo.com/{b['id']}" if b["provider"] == "vimeo" else f"https://www.youtube.com/watch?v={b['id']}"
            out += [url, "", f"*{b['caption']}*"]
        out.append("")
    if srcs:
        out += ["## Nguồn tham khảo", *[f"- [{s['title']}]({s['url']})" + (f" · {s['checkedAt']}" if s.get("checkedAt") else "")
                                        for s in srcs], ""]
    return "\n".join(out)


def write_pack(articles: list[dict], repo: str, name: str, overwrite: bool = False,
               check_gate: bool = True) -> dict[str, Any]:
    """Write `src/lib/lab/packs/<name>.ts`, register it in `PACKS`, then run the site's own gate.

    `articles` are Article dicts or `md_to_article` results. Never pushes: the owner runs
    `push:lab` (drafts only) after reviewing.
    """
    import subprocess
    from pathlib import Path

    if not re.fullmatch(r"[a-z0-9-]+", name or ""):
        return {"ok": False, "problems": ["packName"]}
    packs = Path(repo).expanduser() / "src" / "lib" / "lab" / "packs"
    index = packs / "index.ts"
    if not index.exists():
        return {"ok": False, "problems": [f"not an Alpha ColorLab repo: {index} missing"]}
    pack_file = packs / f"{name}.ts"
    if pack_file.exists() and not overwrite:
        return {"ok": False, "path": str(pack_file), "problems": ["packExists (overwrite=True to replace)"]}

    pages = [a.get("article", a) for a in articles]
    var = re.sub(r"-([a-z0-9])", lambda m: m[1].upper(), name)
    var = var if var[0].isalpha() else f"pack{var}"

    # Backup before writing
    pack_existed = pack_file.exists()
    pack_backup = pack_file.read_text(encoding="utf-8") if pack_existed else None
    index_backup = index.read_text(encoding="utf-8")

    pack_file.write_text(
        "import type { Article } from '../types'\n\n"
        "/** Written by alphaskill (sony-alpha-viet `colorlab_pack`) from Markdown. Edit the Markdown, then rewrite. */\n"
        f"export const {var}: readonly Article[] = {json.dumps(pages, ensure_ascii=False, indent=2)}\n",
        encoding="utf-8")
    src = index.read_text(encoding="utf-8")
    imp = f"import {{ {var} }} from './{name}'\n"
    if imp not in src:
        src = src.replace("import type { Article } from '../types'\n", "import type { Article } from '../types'\n" + imp, 1)
        entry = f"'{name}': {var}"
        if re.search(r"export const PACKS[^=]*=\s*\{\s*\}", src):
            src = re.sub(r"(export const PACKS[^=]*=\s*)\{\s*\}", lambda m: f"{m[1]}{{ {entry} }}", src, count=1)
        else:
            src = re.sub(r"(export const PACKS[^=]*=\s*\{)", lambda m: f"{m[1]}\n  {entry},", src, count=1)
        index.write_text(src, encoding="utf-8")

    out: dict[str, Any] = {
        "ok": True, "path": str(pack_file), "index": str(index), "problems": [],
        "next": ["npx vitest run src/lib/lab/packs",
                 f"npm run push:lab -- --target content --pack {name} --dry-run",
                 f"npm run push:lab -- --target content --pack {name}"]}
    if check_gate:
        r = subprocess.run(["npx", "vitest", "run", "src/lib/lab/packs"], cwd=packs.parents[3],
                           capture_output=True, text=True)
        log = r.stdout + r.stderr
        out["gate"] = "passed" if r.returncode == 0 else "failed"
        out["gate_log"] = "\n".join(log.strip().splitlines()[-30:])
        out["ok"] = r.returncode == 0
        if r.returncode != 0:
            if pack_existed:
                pack_file.write_text(pack_backup, encoding="utf-8")
            else:
                pack_file.unlink(missing_ok=True)
            index.write_text(index_backup, encoding="utf-8")
            out["restored"] = True
    return out
