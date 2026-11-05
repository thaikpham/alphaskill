"""Alpha ColorLab `Article` -> static HTML that matches the site's /blog/<id> page (paper theme).

The markup mirrors the server-rendered output of `src/components/lab/article-view.tsx` and
`blocks.tsx` class for class; the stylesheet is the site's own compiled CSS, pruned to the
classes used here (`colorlab_assets/site.css`, refreshed with `sync_css`). Fonts are the site's
self-hosted Noto Sans subsets, embedded so Vietnamese renders the same anywhere.

    python -m sony_alpha_viet.blog.colorlab_html sync http://localhost:3000/vi/blog/back-button-af
"""
from __future__ import annotations

import base64
import html
import json
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

ASSETS = Path(__file__).with_name("colorlab_assets")
SITE = "https://alphacolorlab.com"
TOPICS = {"setup": "Thiết lập máy", "color": "Màu ảnh & Creative Look", "af": "Lấy nét & AF",
          "exposure": "Phơi sáng & đo sáng", "composition": "Bố cục & ánh sáng", "lens": "Ống kính",
          "body": "Thân máy & so sánh", "video": "Video & quay phim", "audio": "Âm thanh & thu âm",
          "post": "Hậu kỳ & LUT", "gear": "Phụ kiện & quy trình", "firmware": "Firmware"}
LEVELS = {"newbie": "Cơ bản", "mid": "Trung cấp", "pro": "Nâng cao"}
SECTIONS = {"fundamentals": "Nền tảng", "sony-color": "Màu Sony", "workflows": "Quy trình"}
FIRMWARE_NOTE = "Tên mục menu có thể khác đôi chút giữa các bản firmware và giữa các dòng máy. Nếu không thấy đúng tên, tìm mục gần nhất trong cùng nhóm — giá trị cần đặt vẫn như trên."
GAP = "mb-7"


def e(s: str) -> str:
    return html.escape(unicodedata.normalize("NFC", str(s)), quote=True)


def _day(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def _trunc(text: str, n: int = 92) -> str:
    """`truncateOnWord` in outline.ts."""
    clean = re.sub(r"\s+", " ", text.strip())
    if len(clean) <= n:
        return clean
    cut = clean[:n]
    head = cut[:cut.rfind(" ")] if cut.rfind(" ") > 0 else cut
    return re.sub(r"[\s,;:.—–-]+$", "", head) + "…"


def outline(blocks: list[dict]) -> list[dict]:
    """`buildOutline` in outline.ts."""
    from .colorlab import _precis
    heads = [i for i, b in enumerate(blocks) if b["t"] == "h"]
    return [{"n": f"{k + 1:02d}", "id": f"h-{i}", "text": blocks[i]["text"],
             "precis": _trunc(_precis(blocks[i + 1:(heads + [len(blocks)])[k + 1]]))} for k, i in enumerate(heads)]


def _outline_list(items: list[dict]) -> str:
    return '<ul lang="vi" class="mt-1">' + "".join(
        f'<li><hr class="seam"/><a href="#{o["id"]}" class="flex min-h-[var(--layout-touch-target)] gap-2.5 rounded-sm px-2 py-3 '
        f'transition-colors hover:bg-glass"><span class="text-label font-bold tabular-nums text-accent-400">{o["n"]}</span>'
        f'<span class="min-w-0"><span class="block text-body-sm font-semibold leading-[1.35] text-ink">{e(o["text"])}</span>'
        + (f'<span class="meta mt-1 block leading-[1.45]">{e(o["precis"])}</span>' if o["precis"] else "")
        + "</span></a></li>" for o in items) + "</ul>"


def _well(cls: str, inner: str = "") -> str:
    return f'<div class="surface-sunken relative {cls} overflow-hidden rounded-lg">{inner}</div>'


def block(b: dict, i: int) -> str:
    t = b["t"]
    if t == "tldr":
        items = "".join(f'<li class="flex gap-2.5 py-1"><span aria-hidden="true" class="text-accent-300">—</span>'
                        f'<span class="text-body-lg leading-[1.6] text-ink">{e(x)}</span></li>' for x in b["items"])
        return (f'<aside class="{GAP} rounded-lg bg-accent-900 px-6 py-[22px] shadow-[var(--elevation-spec)]">'
                f'<p class="label text-accent-300">Tóm tắt</p><ul class="mt-2">{items}</ul></aside>')
    if t == "h":
        return (f'<h2 id="h-{i}" class="{GAP} mt-12 scroll-mt-6 text-title-2 font-semibold tracking-[-0.02em] '
                f'leading-[1.25] text-ink">{e(b["text"])}</h2>')
    if t == "p":
        return f'<p class="{GAP} text-body-lg leading-[1.75] text-ink [text-wrap:pretty]">{e(b["text"])}</p>'
    if t == "menu":
        cards = (("Menu cũ · a6400 · ZV-E10", b["old"]), ("Menu mới · a6700 · ZV-E10 II", b["new"]))
        return f'<div class="{GAP} flex flex-wrap gap-3">' + "".join(
            f'<div class="surface-sunken flex-1 basis-60 px-4 py-3.5"><p class="label">{e(lab)}</p>'
            f'<p class="mt-1 text-body-sm leading-relaxed break-words text-ink">{e(path)}</p></div>' for lab, path in cards) + "</div>"
    if t == "table":
        widths = ("w-[38%]", "w-[31%]", "w-[31%]")
        head = "".join(f'<th scope="col" class="label px-4 py-3 {w}">{e(c)}</th>' for c, w in zip(b["head"], widths))
        rows = "".join(
            f'<tr{" class=" + chr(34) + "row-tint" + chr(34) if n % 2 else ""}>'
            f'<th scope="row" class="px-4 py-3 text-body-sm font-semibold text-ink">{e(r[0])}</th>'
            + "".join(f'<td class="px-4 py-3 text-body-sm text-ink-muted">{e(c)}</td>' for c in r[1:]) + "</tr>"
            for n, r in enumerate(b["rows"]))
        return (f'<figure class="{GAP}"><figcaption class="meta mb-2">{e(b["caption"])}</figcaption>'
                f'<div class="surface scroll-area overflow-x-auto rounded-md"><table class="w-full min-w-[34rem] '
                f'border-separate border-spacing-0 text-left"><thead><tr class="bg-sunken">{head}</tr></thead>'
                f'<tbody>{rows}</tbody></table></div></figure>')
    if t == "callout":
        return (f'<aside class="{GAP} surface-raised px-[22px] py-5"><p class="text-body-sm font-semibold text-accent-400">'
                f'{e(b["label"])}</p><p class="mt-1.5 text-body text-ink [text-wrap:pretty]">{e(b["text"])}</p></aside>')
    if t == "compare":
        chips = (f'<span class="chip absolute top-3 left-3 bg-black/60 text-white font-semibold">{e(b["beforeLabel"])}</span>'
                 f'<span class="chip absolute top-3 right-3 bg-black/60 text-white font-semibold">{e(b["afterLabel"])}</span>')
        return f'<figure class="{GAP}">{_well("aspect-3/2", chips)}<figcaption class="meta mt-2">{e(b["caption"])}</figcaption></figure>'
    if t == "checklist":
        items = "".join(
            ('<li>' if n == 0 else '<li><hr class="seam"/>')
            + '<label class="flex min-h-[var(--layout-touch-target)] w-full cursor-pointer items-center gap-3 py-2.5 text-left">'
              '<input type="checkbox" class="h-[22px] w-[22px] shrink-0 cursor-pointer accent-[var(--color-accent-500)]"/>'
              f'<span class="text-body-sm text-ink">{e(x)}</span></label></li>' for n, x in enumerate(b["items"]))
        return (f'<section class="{GAP} surface px-5 pt-2 pb-4"><p class="py-3.5 pb-1.5 text-body-sm font-semibold '
                f'text-ink-muted">{e(b["label"])}</p><ul>{items}</ul></section>')
    if t == "figure":
        return f'<figure class="{GAP}">{_well("aspect-3/2")}<figcaption class="meta mt-2">{e(b["caption"])}</figcaption></figure>'
    if t == "embed":
        src = (f"https://www.youtube-nocookie.com/embed/{b['id']}?rel=0" if b["provider"] == "youtube"
               else f"https://player.vimeo.com/video/{b['id']}?dnt=1")
        frame = (f'<iframe src="{e(src)}" title="{e(b["caption"])}" loading="lazy" allow="accelerometer; encrypted-media; '
                 f'picture-in-picture" allowfullscreen class="absolute inset-0 h-full w-full"></iframe>')
        return f'<figure class="{GAP}">{_well("aspect-video", frame)}<figcaption class="meta mt-2">{e(b["caption"])}</figcaption></figure>'
    return ""


def _sources(sources: list[dict]) -> str:
    if not sources:
        return ""
    items = []
    for s in sources:
        from urllib.parse import urlparse
        facts = " · ".join(x for x in (s.get("publisher"), s.get("section"), s.get("scope")) if x)
        when = f"kiểm tra {_day(s['checkedAt'])}" if s.get("checkedAt") else ""
        meta = f'<span class="meta block"><span lang="vi">{e(facts)}</span>{" · " if facts and when else ""}{e(when)}</span>' if facts or when else ""
        url_scheme = urlparse(s["url"]).scheme.lower()
        if url_scheme in ("http", "https"):
            items.append(f'<li class="text-body-sm leading-[1.5]"><a href="{e(s["url"])}" rel="noopener noreferrer" target="_blank" '
                         f'lang="vi" class="font-semibold text-accent-400 underline decoration-accent-400/40 underline-offset-2 '
                         f'transition-colors hover:decoration-accent-400 [overflow-wrap:anywhere]">{e(s["title"])}</a>{meta}</li>')
        else:
            items.append(f'<li class="text-body-sm leading-[1.5]"><span lang="vi" class="font-semibold text-accent-400">{e(s["title"])}</span>{meta}</li>')
    return f'<section aria-label="Nguồn"><h2 class="label">Nguồn</h2><ol class="mt-2 flex flex-col gap-2">{"".join(items)}</ol></section>'


def body(a: dict) -> str:
    knowledge, meta = a["kind"] == "knowledge", a["meta"]
    out = outline(a["blocks"])
    route = "learn" if knowledge else "blog"
    kicker = SECTIONS.get(meta.get("section") or "", "") if knowledge else TOPICS.get(a["topic"], a["topic"])
    facts = ("" if knowledge else f' · {e(LEVELS.get(a["level"], a["level"]))} ') + (f' · <span lang="vi">{e(a["read"])}</span>' if a["read"] else "")
    rail_label = "Trong trang này" if knowledge else "Trong bài viết"
    byline = " · ".join(x for x in (f"Viết bởi {e(meta['authorName'])}" if meta.get("authorName") else "",
                                     f"Rà soát {_day(meta['reviewedAt'])}" if meta.get("reviewedAt") else "") if x)
    phone_nav = (f'<nav aria-label="Tóm tắt và mục lục bài viết" lang="vi" class="mt-8 flex flex-col gap-5 lg:hidden">'
                 f'<details class="group"><summary class="label flex min-h-[var(--layout-touch-target)] cursor-pointer list-none '
                 f'items-center justify-between gap-2 [&amp;::-webkit-details-marker]:hidden">{rail_label}<span aria-hidden="true" '
                 f'class="text-ink-faint group-open:rotate-180">▾</span></summary>{_outline_list(out)}</details></nav>') if out else ""
    rail = (f'<nav aria-label="Tóm tắt và mục lục bài viết" class="hidden lg:flex lg:sticky lg:top-6 shrink-0 '
            f'basis-[clamp(15rem,19vw,20rem)] flex-col gap-5"><div><p class="label">{rail_label}</p>{_outline_list(out)}</div></nav>') if out else ""
    return (
        '<main class="mx-auto min-h-screen-dynamic w-full max-w-[86rem] inset-safe pt-8 pb-24">'
        '<div class="flex flex-col lg:flex-row lg:items-start gap-y-8 gap-x-[clamp(2rem,3.5vw,4rem)]">'
        '<article class="lab-article min-w-0 max-w-[46rem] lg:flex-1 lg:basis-[32.5rem]">'
        f'<a class="mb-6 inline-flex min-h-[var(--layout-touch-target)] items-center gap-2 text-body-sm font-semibold text-ink-muted '
        f'transition-colors hover:text-accent-400" href="{SITE}/vi/{route}"><span aria-hidden="true">←</span>'
        f'<span>{"Kiến thức" if knowledge else "Tất cả bài viết"}</span></a>'
        f'<p class="mb-3 text-label font-semibold text-ink-faint"><span class="text-accent-400">{e(kicker)}</span>'
        f'<span class="text-ink-faint">{facts}</span></p>'
        '<div lang="vi">'
        f'<h1 class="text-display font-semibold tracking-[-0.02em] leading-[1.15] text-ink [text-wrap:pretty]">{e(a["title"])}</h1>'
        + (f'<p class="mt-4 text-title-3 font-normal leading-[1.5] text-ink-muted [text-wrap:pretty]">{e(a["dek"])}</p>' if a["dek"] else "")
        + phone_nav + '<hr class="seam mt-8 mb-8"/>' + "".join(block(b, i) for i, b in enumerate(a["blocks"])) + "</div>"
        '<footer class="mt-3 flex flex-col gap-6 pt-5"><hr class="seam"/>' + _sources(meta.get("sources", []))
        + (f'<p class="meta"><span lang="vi">{byline}</span></p>' if byline else "")
        + f'<p class="meta">{e(FIRMWARE_NOTE)}</p></footer></article>' + rail + "</div></main>")


def header() -> str:
    tab = ("flex min-h-10 items-center gap-1.5 rounded-sm px-2.5 text-body-sm font-semibold transition-colors sm:px-3 ")
    return (
        '<header class="sticky top-0 z-40"><div class="mx-auto max-w-[160rem] inset-safe pt-safe">'
        '<div class="header-bar rounded-xl bg-[linear-gradient(180deg,oklch(100%_0_0/0.075),oklch(100%_0_0/0.035))] '
        '[backdrop-filter:var(--elevation-blur-strong)] [-webkit-backdrop-filter:var(--elevation-blur-strong)] '
        'shadow-[0_14px_34px_-18px_oklch(0%_0_0/0.9),var(--elevation-spec)] px-3 py-2 sm:px-6 sm:py-3 flex flex-col">'
        '<div class="flex flex-nowrap items-center justify-between gap-2 sm:gap-4">'
        f'<a class="flex min-h-[var(--layout-touch-target)] min-w-0 items-center gap-2 sm:gap-2.5" href="{SITE}/vi/blog">'
        '<span class="flex items-center gap-1.5 truncate whitespace-nowrap text-body-lg font-extrabold tracking-[-0.02em] text-ink">'
        'ALPHA TECH <span class="text-accent-400">BLOGS</span></span></a>'
        '<div class="surface-sunken shrink-0 items-center gap-1 p-0.5 hidden sm:flex">'
        f'<a class="{tab}surface-selected text-ink" href="{SITE}/vi/blog">Bài viết</a>'
        f'<a class="{tab}text-ink-muted hover:text-ink" href="{SITE}/vi/learn">Kiến thức</a></div></div></div></div></header>')


@lru_cache(maxsize=1)
def _fonts() -> str:
    ranges = {
        "latin": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, "
                 "U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
        "vietnamese": "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, "
                      "U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB"}
    return "".join(
        "@font-face{font-family:'Noto Sans';font-style:normal;font-weight:400 800;font-display:swap;"
        f"src:url(data:font/woff2;base64,{base64.b64encode((ASSETS / f'NotoSans-{k}.woff2').read_bytes()).decode()}) format('woff2');"
        f"unicode-range:{v}}}" for k, v in ranges.items())


def _scope(css: str, root: str) -> str:
    """Re-root the site stylesheet under `root` so a pasted fragment cannot restyle its host page."""
    def one(sel: str) -> str:
        sel = re.sub(r":root:has\(\.theme-paper\)", root, sel)
        sel = re.sub(r"^(?::root|:host|html|body)(?![\w-])", root, sel)
        return sel if sel.startswith(root) else f"{root} {sel}"
    return _walk(css, one, unlayer=True)


def render_article(article: dict, *, standalone: bool = True) -> str:
    css = (ASSETS / "site.css").read_text(encoding="utf-8")
    page = body(article)
    if not standalone:
        return (f'<div class="clab theme-paper" lang="vi"><style>{_fonts()}{_scope(css, ".clab")}</style>'
                f'{page}</div>')
    a, route = article, "learn" if article["kind"] == "knowledge" else "blog"
    url = f"{SITE}/vi/{route}/{a['id']}"
    faq = [{"@type": "Question", "name": b["text"], "acceptedAnswer": {"@type": "Answer", "text": nxt["text"]}}
           for b, nxt in zip(a["blocks"], a["blocks"][1:]) if b["t"] == "h" and b["text"].rstrip().endswith("?") and nxt["t"] == "p"]
    graph = [{"@type": "Article", "headline": a["title"], "description": a["dek"], "inLanguage": "vi", "mainEntityOfPage": url,
              "author": {"@type": "Person", "name": a["meta"]["authorName"]} if a["meta"].get("authorName") else {"@type": "Organization", "name": "Alpha ColorLab"},
              "publisher": {"@type": "Organization", "name": "Alpha ColorLab", "url": SITE},
              **({"dateModified": a["meta"]["reviewedAt"]} if a["meta"].get("reviewedAt") else {})}]
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": faq})
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
    return (
        '<!doctype html><html lang="vi" class="h-full antialiased"><head><meta charset="utf-8"/>'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>'
        f'<title>{e(a["title"])} · Alpha ColorLab</title><meta name="description" content="{e(a["dek"])}"/>'
        f'<link rel="canonical" href="{e(url)}"/><style>{_fonts()}{css}</style>'
        f'<script type="application/ld+json">{ld}</script></head>'
        '<body class="app-shell font-sans min-h-screen-dynamic flex flex-col"><div class="theme-paper contents">'
        f'{header()}{page}</div></body></html>')


# --- refreshing the vendored stylesheet from the site -------------------------------------------

def _classes(markup: str) -> set[str]:
    return {c for attr in re.findall(r'class="([^"]*)"', html.unescape(markup)) for c in attr.split()}


def _walk(css: str, fn, unlayer: bool = False) -> str:
    """Apply `fn` to every selector of every style rule (None drops it); recurse into grouping at-rules.
    `unlayer` drops `@layer` wrappers: inside a host page, layered rules lose to any unlayered host CSS."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, i = [], 0
    while i < len(css):
        j = css.find("{", i)
        if j < 0:
            out.append(css[i:].strip())
            break
        k, depth = j + 1, 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        pre, _, head = css[i:j].strip().rpartition(";")
        inner = css[j + 1:k - 1]
        if pre.strip() and not (unlayer and pre.strip().startswith("@layer")):
            out.append(pre.strip() + ";")
        head = head.strip()
        if head.startswith(("@font-face", "@import")):
            pass
        elif head.startswith(("@layer", "@media", "@supports", "@container")):
            kept = _walk(inner, fn, unlayer)
            if kept.strip():
                out.append(kept if unlayer and head.startswith("@layer") else f"{head}{{{kept}}}")
        elif head.startswith("@"):
            out.append(f"{head}{{{inner}}}")
        else:
            parts = [q for q in (fn(p.strip()) for p in re.split(r",(?![^()]*\))", head)) if q]
            if parts:
                out.append(f"{','.join(parts)}{{{inner.strip()}}}")
        i = k
    return "\n".join(x for x in out if x)


def _prune(css: str, used: set[str]) -> str:
    """Keep only the selectors whose every class is one the renderer emits."""
    return _walk(css, lambda sel: sel if {re.sub(r"\\(.)", r"\1", c) for c in re.findall(r"\.((?:\\.|[\w-])+)", sel)} <= used else None)


def sync_css(page_url: str) -> dict:
    """Fetch a rendered /blog page from a running site (offline seed mode is fine), prune its CSS to the
    classes this renderer emits, and write `colorlab_assets/site.css`."""
    import urllib.request
    from urllib.parse import urljoin
    page = urllib.request.urlopen(page_url).read().decode()
    css = "".join(urllib.request.urlopen(urljoin(page_url, href)).read().decode()
                  for href in re.findall(r'href="([^"]+\.css[^"]*)"', page))
    sample = json.loads((Path(__file__).resolve().parents[3] / "tests/fixtures/colorlab-site-articles.json").read_text(encoding="utf-8")) \
        if (Path(__file__).resolve().parents[3] / "tests/fixtures/colorlab-site-articles.json").exists() else []
    kinds = [{"t": t} for t in ("tldr", "h", "p", "menu", "table", "callout", "compare", "checklist", "figure", "embed")]
    used = _classes(header()) | {"theme-paper", "contents", "app-shell", "font-sans", "min-h-screen-dynamic", "flex",
                                 "flex-col", "h-full", "antialiased", "row-tint", "lab-article"}
    for a in sample:
        used |= _classes(body(a))
    used |= _classes(body({"id": "x", "kind": "knowledge", "topic": "af", "level": "mid", "archetype": "explainer", "read": "x",
                           "title": "x", "dek": "x", "meta": {"sources": [{"url": "u", "title": "t", "publisher": "p", "checkedAt": "2026-01-01"}],
                                                             "authorName": "a", "reviewedAt": "2026-01-01", "section": "workflows"},
                           "blocks": [dict(k, text="x?", items=["a", "b", "c"], old="MENU → a", new="MENU → b", head=["a", "b", "c"],
                                           rows=[["a", "b", "c"], ["d", "e", "f"]], caption="c", label="l", beforeLabel="a",
                                           afterLabel="b", provider="youtube", id="x") for k in kinds]}))
    pruned = _prune(css, used)
    (ASSETS / "site.css").write_text(f"/* Pruned from {page_url} by colorlab_html.sync_css. Do not edit by hand. */\n{pruned}\n", encoding="utf-8")
    return {"source_bytes": len(css), "pruned_bytes": len(pruned), "classes": len(used)}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "sync":
        print(sync_css(sys.argv[2]))
    else:
        print(__doc__)
