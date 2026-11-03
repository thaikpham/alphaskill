"""Alpha ColorLab Article -> HTML (blog/colorlab_html.py)."""
import json
import re
from pathlib import Path

from sony_alpha_viet.blog.colorlab import md_to_article
from sony_alpha_viet.blog.colorlab_html import _prune, _scope, outline, render_article

FIX = Path(__file__).parent / "fixtures"
SITE = {a["id"]: a for a in json.loads((FIX / "colorlab-site-articles.json").read_text(encoding="utf-8"))}
POST = md_to_article((FIX / "colorlab-post.md").read_text(encoding="utf-8"))["article"]


def test_standalone_page():
    h = render_article(POST)
    assert h.startswith("<!doctype html>") and '<html lang="vi"' in h and 'class="theme-paper contents"' in h
    assert '<link rel="canonical" href="https://alphacolorlab.com/vi/blog/lay-net-bang-ngon-tay-cai"/>' in h
    assert h.count("@font-face") == 2 and "data:font/woff2;base64," in h and "U+1EA0-1EF9" in h
    assert "fonts.googleapis" not in h and re.findall(r"<script(?! type=\"application/ld\+json\")", h) == []
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', h).group(1))
    kinds = [g["@type"] for g in ld["@graph"]]
    assert kinds == ["Article", "FAQPage"]
    assert ld["@graph"][1]["mainEntity"][0]["name"].startswith("Có cần tắt AF w/ Shutter")


def test_markup_mirrors_site_components():
    h = render_article(SITE["back-button-af"])
    assert '<aside class="mb-7 rounded-lg bg-accent-900' in h and '<p class="label text-accent-300">Tóm tắt</p>' in h
    assert '<h2 id="h-2" class="mb-7 mt-12' in h                      # anchors = headingId(blockIndex)
    assert "Menu cũ · a6400 · ZV-E10" in h and "Menu mới · a6700 · ZV-E10 II" in h
    assert '<tr class="row-tint">' in h and 'class="surface scroll-area' in h
    assert "lg:sticky lg:top-6" in h and "Trong bài viết" in h       # desktop rail + phone outline
    assert [o["id"] for o in outline(SITE["back-button-af"]["blocks"])] == ["h-2", "h-6"]


def test_knowledge_page_and_sources():
    h = render_article(SITE["white-balance-shift"])
    assert "https://alphacolorlab.com/vi/learn/white-balance-shift" in h and "Trong trang này" in h
    assert '<h2 class="label">Nguồn</h2>' in h and "kiểm tra 05/10/2026" in h


def test_escaping_and_nfc():
    a = json.loads(json.dumps(POST))
    a["title"] = "A <b> & Ưu tiên khẩu độ"   # decomposed input is normalised to NFC
    a["blocks"][1]["text"] = "<script>alert(1)</script>"
    h = render_article(a)
    assert "<script>alert" not in h and "&lt;script&gt;" in h and "A &lt;b&gt; &amp; Ưu tiên khẩu độ" in h


def test_fragment_is_scoped_and_unlayered():
    f = render_article(POST, standalone=False)
    assert f.startswith('<div class="clab theme-paper" lang="vi"><style>') and "<html" not in f
    css = re.search(r"<style>(.*)</style>", f, re.S).group(1)
    assert "@layer" not in css and ":root" not in css
    selectors = [s.strip() for s in re.findall(r"(?:^|})\s*([^{}@]+)\{", re.sub(r"@font-face\{[^}]*\}", "", css))]
    assert selectors and all(s.startswith(".clab") or re.match(r"^(from|to|\d+%)", s) for s in selectors)


def test_prune_and_scope():
    css = "@layer a,b;@layer a{:root{--x:1}.keep{color:red}.drop{color:blue}.keep:hover,.gone .keep{x:y}}@media (w>1px){.keep{a:b}}"
    pruned = _prune(css, {"keep"})
    assert ".drop" not in pruned and ".gone" not in pruned and ".keep:hover" in pruned and ":root{--x:1}" in pruned
    assert _scope(":root:has(.theme-paper){--y:2} .keep{a:b}", ".clab") == ".clab{--y:2}\n.clab .keep{a:b}"
