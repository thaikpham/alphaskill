"""Blog/doc mode tools: slugify, word count, prose term lookup, style lint, SEO audit, FAQ schema."""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

from ._doc import BULLET_RX, STRUCT_RX, as_article, count_words, fold, links, normalize, quote, tldr
from .aio_audit import aio_audit, check_sourced_numbers
from .audit import blog_audit
from .brand_voice_checker import brand_voice_checker
from .citation_checker import citation_checker
from .colorlab import md_to_article, write_pack
from .freshness_check import freshness_check
from .paa_generator import paa_generator

__all__ = [
    "aio_audit",
    "blog_audit",
    "brand_voice_checker",
    "citation_checker",
    "count_words",
    "faq_schema",
    "freshness_check",
    "lookup_prose_term",
    "md_to_article",
    "paa_generator",
    "seo_audit",
    "slugify",
    "style_lint",
    "write_pack",
]

# Read skill resources at runtime
def _get_skill_root() -> Path:
    """Locate skill dir relative to package root (repo root = parent of src)."""
    for p in (Path(__file__).resolve().parents[3], Path(__file__).resolve().parents[2]):
        candidate = p / "skills" / "sony-alpha-viet"
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parents[3] / "skills" / "sony-alpha-viet"

def _load_glossary_vi() -> dict:
    """Load glossary-vi.md and parse markdown table: returns {en.lower(): {en, jp, menu, prose, note}}."""
    glossary_file = _get_skill_root() / "references" / "glossary-vi.md"
    if not glossary_file.exists():
        return {}

    content = glossary_file.read_text(encoding="utf-8")
    result = {}

    # Parse markdown tables: line with | separators after ## sections
    for line in content.split("\n"):
        if line.startswith("##"):
            continue
        if not line.startswith("|"):
            continue

        # Parse row: | EN | JP | Menu OSD | Bài viết/Tài liệu | Ghi chú |
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 3 or cells[0] in ("EN", "---"):
            continue

        en = cells[0].replace(" 🔒", "").strip()
        jp = cells[1] if len(cells) > 1 else ""
        menu = cells[2].replace(" 🔒", "").strip() if len(cells) > 2 else ""
        prose = cells[3].replace(" 🔒", "").strip() if len(cells) > 3 else ""
        note = cells[4] if len(cells) > 4 else ""

        if en and en != "---":
            result[en.lower()] = {
                "en": en,
                "jp": jp,
                "menu": menu,
                "prose": prose,
                "note": note
            }
    return result

def _load_ai_sounding_phrases() -> set[str]:
    """Load 'AI-sounding' phrases from writing-style-vi.md, comma-separated after heading."""
    style_file = _get_skill_root() / "references" / "writing-style-vi.md"
    if not style_file.exists():
        return set()

    content = style_file.read_text(encoding="utf-8")
    phrases = set()

    # Find section: ## Cụm "AI-sounding" cần tránh
    in_section = False
    for line in content.split("\n"):
        if '## Cụm "AI-sounding"' in line:
            in_section = True
            continue
        if line.startswith("##") and in_section:
            break
        if in_section and line.strip():
            # Parse comma-separated phrases in quotes
            for match in re.finditer(r'"([^"]+)"', line):
                phrases.add(match.group(1))

    return phrases

# === Core functions ===

def slugify(text: str, max_words: int = 6) -> str:
    """Vietnamese → ASCII lowercase hyphen slug. đ→d, strip diacritics, collapse hyphens."""
    # Remove diacritics
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Replace đ/Đ with d/D
    text = text.replace("đ", "d").replace("Đ", "D")
    # Lowercase, keep alphanumeric and hyphens
    text = re.sub(r"[^a-z0-9\-]", "-", text.lower())
    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    # Limit to max_words
    if max_words:
        words = text.split("-")
        text = "-".join(words[:max_words])
    return text

def lookup_prose_term(query: str) -> list[dict]:
    """Fuzzy lookup (case-insensitive substring) on EN/JP/menu/prose columns."""
    glossary = _load_glossary_vi()
    query_lower = query.lower()
    results = []

    for entry in glossary.values():
        if (query_lower in entry["en"].lower() or
            query_lower in entry["jp"].lower() or
            query_lower in entry["menu"].lower() or
            query_lower in entry["prose"].lower()):
            results.append({
                "en": entry["en"],
                "jp": entry["jp"],
                "menu": entry["menu"],
                "prose": entry["prose"],
                "note": entry["note"]
            })

    return results

BANNED_PROSE = [
    (r"khung hình đầy đủ", "Full-frame: viết \"full-frame\""),
    (r"cửa trập|màn chập|cửa chập", "Shutter = màn trập"),
    (r"nút màn trập", "Shutter Button = nút chụp"),
    (r"nhận diện chủ thể", "Subject Recognition = nhận dạng chủ thể"),
    (r"màn trập cơ học", "Mechanical Shutter = màn trập cơ"),
    (r"(?<!\w)dò (?:theo|nét)", "Tracking = theo dõi"),
]


def _strip_special_regions(text: str) -> tuple[str, dict]:
    """Return (stripped text, {region_id: (start, end)}) for code/inline/urls to skip checks."""
    regions = {}

    # Fenced code blocks
    for m in re.finditer(r"```.*?```", text, re.DOTALL):
        rid = f"code_{len(regions)}"
        regions[rid] = (m.start(), m.end())

    # Inline code
    for m in re.finditer(r"`[^`]+`", text):
        if not any(m.start() >= r[0] and m.end() <= r[1] for r in regions.values()):
            rid = f"inline_{len(regions)}"
            regions[rid] = (m.start(), m.end())

    # URLs
    for m in re.finditer(r"https?://[^\s\)\]>\"']+", text):
        if not any(m.start() >= r[0] and m.end() <= r[1] for r in regions.values()):
            rid = f"url_{len(regions)}"
            regions[rid] = (m.start(), m.end())

    # Markdown table rows
    for m in re.finditer(r"^\|[^|]*\|.*$", text, re.MULTILINE):
        if not any(m.start() >= r[0] and m.end() <= r[1] for r in regions.values()):
            rid = f"table_{len(regions)}"
            regions[rid] = (m.start(), m.end())

    return text, regions

def _is_in_region(pos: int, regions: dict) -> bool:
    """Check if position is inside any protected region."""
    return any(r[0] <= pos < r[1] for r in regions.values())


REDUPLICATIVES = {"từ", "song", "dần", "đâu", "ai", "gì", "nhiều", "lâu", "xa", "mãi", "đều", "khác", "mỗi", "cùng", "nhè", "vừa", "tận"}


def style_lint(text: str) -> dict:
    """Lint for style issues: AI-sounding phrases, passive voice, sentence length, etc."""
    issues = []
    ai_phrases = _load_ai_sounding_phrases()
    _, protected_regions = _strip_special_regions(text)

    # Check for AI-sounding phrases
    for phrase in ai_phrases:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        for match in pattern.finditer(text):
            if _is_in_region(match.start(), protected_regions):
                continue
            line_no = text[:match.start()].count("\n") + 1
            issues.append({
                "type": "ai_sounding",
                "match": phrase,
                "line": line_no,
                "hint": f"Tránh cụm: {phrase}"
            })

    # Check for passive voice: "được ... bởi"
    for match in re.finditer(r"được\s+\w+\s+bởi", text):
        if _is_in_region(match.start(), protected_regions):
            continue
        line_no = text[:match.start()].count("\n") + 1
        issues.append({
            "type": "passive",
            "match": match.group(0),
            "line": line_no,
            "hint": "Dùng chủ động thay vì bị động"
        })

    # Em dash, or spaced en dash, as a clause connector; unspaced en dash is a range (F8–F11, 5–15s)
    for match in re.finditer(r"—|(?<= )–(?= )", text):
        if _is_in_region(match.start(), protected_regions):
            continue
        if text[max(0, match.start() - 2):match.start()].strip() or text[match.end():match.end() + 2].strip():
            line_no = text[:match.start()].count("\n") + 1
            issues.append({
                "type": "dash",
                "match": match.group(0),
                "line": line_no,
                "hint": "Dùng dấu chấm, phẩy, hoặc hai chấm thay vì gạch dài"
            })

    # Check for "không phải...mà là" and "không chỉ...mà còn" patterns
    for match in re.finditer(r"không\s+(?:phải|chỉ)\s*(?:là)?\s*[^.!?]*?\s+mà\s+(?:là|còn)\s+", text, re.IGNORECASE):
        if _is_in_region(match.start(), protected_regions):
            continue
        # Skip if this is part of the brand closer "Chọn Sony không chỉ"
        start_context = max(0, match.start() - 50)
        if "Chọn Sony không chỉ" in text[start_context:match.start() + 100]:
            continue
        line_no = text[:match.start()].count("\n") + 1
        issues.append({
            "type": "not_x_but_y",
            "match": match.group(0)[:40],
            "line": line_no,
            "hint": "Cấu trúc 'không phải...mà là' lặp lại. Nói thẳng thay vì dùng cấu trúc đối lập."
        })

    # Check for "Việc " at start of sentence
    for match in re.finditer(r"(?:^|\n)\s*Việc\s+", text):
        line_no = text[:match.start()].count("\n") + 1
        issues.append({
            "type": "viec_prefix",
            "match": "Việc",
            "line": line_no,
            "hint": "Bỏ 'Việc' ở đầu câu"
        })

    # Check sentence length > 35 words
    for i, para in enumerate(text.split("\n")):
        for j, sent in enumerate(re.split(r"[.!?]", para)):
            words = len(sent.split())
            if words > 35:
                line_no = text[:text.find(sent)].count("\n") + 1
                issues.append({
                    "type": "long_sentence",
                    "match": sent.strip()[:50],
                    "line": line_no,
                    "hint": f"Câu dài {words} từ, tách đôi"
                })

    # Check "của" ≥3 times in a sentence
    for para in text.split("\n"):
        for sent in re.split(r"[.!?]", para):
            if sent.count("của") >= 3:
                line_no = text[:text.find(sent)].count("\n") + 1
                issues.append({
                    "type": "multi_của",
                    "match": "của",
                    "line": line_no,
                    "hint": f"Quá nhiều 'của' ({sent.count('của')} lần), rút gọn câu"
                })

    # Check doubled words. Vietnamese reduplicatives ("từ từ", "song song") are words, not typos.
    for match in re.finditer(r"\b(\w+)\s+\1\b", text):
        if match.group(1).lower() in REDUPLICATIVES:
            continue
        line_no = text[:match.start()].count("\n") + 1
        issues.append({
            "type": "doubled",
            "match": match.group(0),
            "line": line_no,
            "hint": "Từ lặp lại"
        })

    # Check decimal point in prose numbers (not in f/2.8, 0.3EV, version)
    for match in re.finditer(r"\b(\d+)\.(\d+)\s+(stop|f/)", text):
        line_no = text[:match.start()].count("\n") + 1
        issues.append({
            "type": "decimal_point",
            "match": match.group(0),
            "line": line_no,
            "hint": f"Dùng dấu phẩy: {match.group(1)},{match.group(2)} thay vì {match.group(1)}.{match.group(2)}"
        })

    # Banned prose terms (glossary-vi.md, writing-style-vi.md)
    for rx, hint in BANNED_PROSE:
        for match in re.finditer(rx, text, re.IGNORECASE):
            issues.append({"type": "terminology", "match": match.group(0), "line": text[:match.start()].count("\n") + 1, "hint": hint})

    # Count [cần xác minh] markers
    verify_count = len(re.findall(r"\[cần xác minh\]", text))
    if verify_count > 0:
        issues.append({
            "type": "verify_markers",
            "match": "[cần xác minh]",
            "line": -1,
            "hint": f"Có {verify_count} mục cần xác minh"
        })

    return {"issues": issues}


# ---------------- SEO / AIO audit ----------------
REQUIRED = {1, 6, 8, 11, 15}


def _norm(s: str) -> str:
    return " ".join(normalize(s).split()).lower()


def seo_audit(markdown: str, primary_keyword: str = "", secondary_keywords: Optional[list[str]] = None) -> dict:
    """Chấm bài theo references/seo-aio-checklist.md: id 1–23 giữ nguyên, 24–26 thêm mới. Mục không chấm bằng máy được → "Cần người duyệt"."""
    a = as_article(markdown)
    fm = a.fm
    kw = (primary_keyword or fm.get("primary_keyword") or "").strip()
    kwf = fold(kw)
    prose = a.prose
    items = []

    def add(i, item, status, evidence="", fix="", hits=()):
        first = hits[0] if hits else (0, "")
        items.append({"id": i, "item": item, "status": status, "required": i in REQUIRED, "evidence": evidence,
                      "fix": fix if status != "Đạt" else "", "line": first[0], "quote": first[1], "occurrences": len(hits)})

    h1s = [h[2] for h in a.headings if h[1] == 1]
    h2s = [h[2] for h in a.headings if h[1] == 2]
    title, desc, slug = fm.get("meta_title", ""), fm.get("meta_description", ""), fm.get("slug", "")
    first100 = fold(" ".join(re.sub(r"[#*_>|`\[\]]", " ", prose).split()[:100]))

    # 1. keyword placement
    if not kw:
        add(1, "Từ khóa chính ở H1, slug, 100 từ đầu, H2, meta description", "Chưa đạt", "Không có từ khóa chính", "Truyền primary_keyword hoặc khai báo trong frontmatter")
    else:
        where = {"H1": any(kwf in fold(h) for h in h1s), "slug": slugify(kw, 20) in slug,
                 "100 từ đầu": kwf in first100, "H2": any(kwf in fold(h) for h in h2s), "meta description": kwf in fold(desc)}
        miss = [k for k, v in where.items() if not v]
        add(1, "Từ khóa chính ở H1, slug, 100 từ đầu, H2, meta description", "Đạt" if not miss else "Chưa đạt",
            "; ".join(f"{k}={'có' if v else 'thiếu'}" for k, v in where.items()), "Thêm từ khóa vào: " + ", ".join(miss))

    # 2–4. meta + slug
    add(2, "Meta title 50–60 ký tự", "Đạt" if 50 <= len(title) <= 60 else "Chưa đạt",
        f"{len(title)} ký tự" if title else "Thiếu meta_title", "Viết lại meta title trong khoảng 50–60 ký tự, từ khóa ở nửa đầu")
    add(3, "Meta description 140–160 ký tự", "Đạt" if 140 <= len(desc) <= 160 else "Chưa đạt",
        f"{len(desc)} ký tự" if desc else "Thiếu meta_description", "Viết lại trong khoảng 140–160 ký tự, có lợi ích + hành động")
    slug_ok = bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)) and len(slug.split("-")) <= 6
    add(4, "Slug không dấu, gạch nối, ≤ 6 từ", "Đạt" if slug_ok else "Chưa đạt", f"'{slug}'", f"Gợi ý: {slugify(kw or (h1s[0] if h1s else ''))}")

    # 5. density = occurrences / words
    words = count_words(markdown)
    occ = len(re.findall(re.escape(kwf), fold(prose))) if kw else 0
    dens = occ / words * 100 if words else 0
    add(5, "Không nhồi từ khóa (≤ 1,5%)", "Đạt" if kw and dens <= 1.5 else ("N/A" if not kw else "Chưa đạt"),
        f"{occ} lần / {words} từ = {dens:.2f}%".replace(".", ","), "Giảm số lần lặp cụm từ khóa chính, dùng biến thể")

    # 6. TL;DR (bullet hoặc đoạn đều đếm như nhau, xem _doc.tldr)
    t = tldr(a)
    add(6, "TL;DR 40–70 từ ngay sau H1", "Đạt" if t["labelled"] and 40 <= t["words"] <= 70 else "Chưa đạt",
        f"{t['words']} từ ({t['form']})" if t["labelled"] else "Không có nhãn TL;DR ngay dưới H1",
        "Thêm/sửa TL;DR 40–70 từ trả lời thẳng câu hỏi chính", [(t["line"], t["quote"])] if t["line"] else [])

    # 7. headings
    levels = [h[1] for h in a.headings]
    jumps = [f"H{x}→H{y}" for x, y in zip(levels, levels[1:]) if y > x + 1]
    add(7, "Một H1; heading không nhảy cấp", "Đạt" if len(h1s) == 1 and not jumps else "Chưa đạt",
        f"{len(h1s)} H1" + (f"; nhảy cấp: {', '.join(jumps)}" if jumps else ""), "Giữ đúng một H1, không bỏ cấp heading")

    # 8. structure
    table = bool(a.tables())
    lst = any(BULLET_RX.match(ln) for ln in a.lines)
    add(8, "Có bảng, checklist hoặc danh sách", "Đạt" if table or lst else "Chưa đạt",
        f"bảng={'có' if table else 'không'}; danh sách={'có' if lst else 'không'}", "Thêm bảng so sánh hoặc danh sách các bước")

    # 9. paragraph length (chỉ dòng văn xuôi: bỏ heading, bullet, task list, bảng, trích dẫn)
    long_p = []
    for blk in a.blocks():
        prose_lines = [(ln, raw.strip()) for ln, raw in blk if not STRUCT_RX.match(raw.strip())]
        if not prose_lines:
            continue
        text = " ".join(raw for _, raw in prose_lines)
        if len(re.findall(r"[.!?](?:\s|$)", text)) > 4:
            long_p.append((prose_lines[0][0], quote(text)))
    add(9, "Đoạn ≤ 4 câu; mỗi H2 mở bằng câu trả lời ngắn", "Đạt" if not long_p else "Một phần",
        f"{len(long_p)} đoạn > 4 câu", "Tách đoạn dài; mở mỗi H2 bằng câu trả lời 1–2 câu", long_p)
    add(10, "Kết luận có hành động cụ thể", "Cần người duyệt", "Có H2 kết luận" if any(re.search(r"ket luan|tom lai|nen chon", fold(h)) for h in h2s) else "Không thấy H2 kết luận",
        "Kết thúc bằng khuyến nghị theo nhóm người dùng + bước tiếp theo")

    # 11. FAQ
    faq = a.faq()
    lens = [f["words"] for f in faq]
    bad_ctx = [f["q"] for f in faq if re.search(r"nhu da noi|o tren|phia tren", fold(f["a"]))]
    ok = 3 <= len(faq) <= 6 and all(40 <= x <= 70 for x in lens) and not bad_ctx
    add(11, "FAQ 3–6 câu, mỗi câu trả lời 40–70 từ, tự đứng được", "Đạt" if ok else ("Chưa đạt" if not faq else "Một phần"),
        f"{len(faq)} câu; số từ={lens}" + (f"; phụ thuộc ngữ cảnh: {bad_ctx}" if bad_ctx else ""),
        "Chỉnh số câu hỏi/độ dài; bỏ tham chiếu 'như đã nói ở trên'", [(f["line"], quote(f["q"])) for f in faq])
    add(12, "Có định nghĩa một câu cho khái niệm chính", "Đạt" if re.search(r"\b(?:la|duoc hieu la)\b", fold(prose)) else "Cần người duyệt", "", "Thêm câu 'X là …' cho khái niệm chính")
    add(13, "Câu số liệu nêu rõ chủ thể và đơn vị", "Cần người duyệt", "", "Kiểm các câu có số: tránh 'nó', 'máy này'")
    add(14, "Có trải nghiệm/bối cảnh riêng (Việt Nam)", "Cần người duyệt", "", "Thêm ví dụ thực tế: địa điểm, giá, dịch vụ, thói quen chụp")

    # 15. unverified: liệt kê từng dòng có [cần xác minh]
    marks = [(ln, quote(raw)) for ln, raw in a.grep(r"\[can xac minh")]
    add(15, "Không có thông số/giá chưa kiểm chứng", "Đạt" if not marks else "Chưa đạt",
        f"{len(marks)} dòng có [cần xác minh]" + (f": dòng {', '.join(str(ln) for ln, _ in marks)}" if marks else ""),
        "Đối chiếu nguồn chính thức rồi bỏ đánh dấu", marks)

    # 16–18. links (nguồn chung với tiêu chí 5), author
    lk = links(a)
    ext = [x for x in lk if not x["internal"]]
    inner = [x for x in lk if x["internal"]]
    n_ph = sum(1 for x in inner if x["kind"] == "placeholder")
    add(16, "Link ngoài 1–3 nguồn uy tín", "Đạt" if 1 <= len(ext) <= 3 else ("Một phần" if ext else "Chưa đạt"),
        f"{len(ext)} link ngoài: " + ", ".join(x["url"][:60] for x in ext[:3]),
        "Giữ 1–3 nguồn mạnh nhất (ưu tiên trang Sony chính thức)",
        [(ln, quote(a.lines[ln - 1])) for ln in sorted({x["line"] for x in ext})])
    add(17, "Link nội bộ 2–5", "Đạt" if 2 <= len(inner) <= 5 else ("Một phần" if inner else "Chưa đạt"),
        f"{len(inner)} link nội bộ, {n_ph} placeholder [link nội bộ: …]",
        "Thêm/giữ 2–5 link nội bộ; thay placeholder [link nội bộ: …] bằng URL thật",
        [(ln, quote(a.lines[ln - 1])) for ln in sorted({x["line"] for x in inner})])
    add(18, "Tác giả và ngày cập nhật", "Đạt" if fm.get("author") and fm.get("updated") else "Chưa đạt",
        f"author={fm.get('author', '')}; updated={fm.get('updated', '')}", "Thêm author, updated vào frontmatter")

    # 19 (→ tiêu chí 26): có đủ kiểu schema; 26 (→ tiêu chí 27): Q/A khớp nguyên văn. Không có JSON-LD: N/A
    nodes = a.jsonld
    types = {n.get("@type") for n in nodes}
    errs = [n["_error"] for n in nodes if "_error" in n]
    schema_faq = []
    for n in nodes:
        if n.get("@type") == "FAQPage":
            schema_faq = [{"q": e.get("name", ""), "a": (e.get("acceptedAnswer") or {}).get("text", "")} for e in n.get("mainEntity", [])]
    mismatch = [f["q"] for f, s in zip(faq, schema_faq) if _norm(f["q"]) != _norm(s["q"]) or _norm(f["a"]) != _norm(s["a"])]
    if len(faq) != len(schema_faq):
        mismatch.append(f"số câu: bài {len(faq)} / Schema {len(schema_faq)}")
    need_howto = bool(re.search(r"huong dan|cach cai|tung buoc", fold(h1s[0]) if h1s else ""))
    missing = [t for t in ("Article", "FAQPage") if t not in types] + (["HowTo"] if need_howto and "HowTo" not in types else [])
    name19 = "Schema Article + FAQPage (+ HowTo nếu hướng dẫn)"
    if not nodes:
        add(19, name19, "N/A", "Không có JSON-LD trong bài")
    else:
        add(19, name19, "Đạt" if not errs and not missing else "Một phần",
            f"types={sorted(t for t in types if t)}" + (f"; lỗi={errs}" if errs else "") + (f"; thiếu: {', '.join(missing)}" if missing else ""),
            f"Sinh lại bằng faq_schema(), đặt khối JSON-LD cuối bài (còn thiếu: {', '.join(missing) or 'sửa lỗi cú pháp'})")

    # 20. images
    imgs = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", prose)
    no_alt = [src for alt, src in imgs if not alt.strip()]
    add(20, "Ảnh có alt text", "N/A" if not imgs else ("Đạt" if not no_alt else "Chưa đạt"), f"{len(imgs)} ảnh, {len(no_alt)} thiếu alt", "Thêm alt mô tả tiếng Việt")

    # 21–22. terminology + style
    lint = style_lint(prose)["issues"]
    term = [i for i in lint if i["type"] == "terminology"]
    style = [i for i in lint if i["type"] not in ("terminology", "verify_markers")]
    add(21, "Thuật ngữ đúng glossary", "Đạt" if not term else "Chưa đạt", "; ".join(f"dòng {i['line']}: {i['match']}" for i in term[:5]),
        "; ".join(i["hint"] for i in term[:3]), [(i["line"], quote(i["match"])) for i in term])
    add(22, "Không văn dịch máy / cụm AI-sounding", "Đạt" if not style else "Một phần", f"{len(style)} vấn đề: " + "; ".join(f"{i['type']}:{i['match'][:30]}" for i in style[:5]),
        "Sửa theo style_lint()")
    add(23, "Không khuyến nghị y tế/tài chính/pháp lý thiếu căn cứ", "Cần người duyệt", "", "")

    # 24. H1 một dòng, không quá dài
    h1_title = h1s[0] if h1s else ""
    add(24, "H1 đúng một dòng, ≤ 70 ký tự", "Đạt" if len(h1s) == 1 and 0 < len(h1_title) <= 70 else "Chưa đạt",
        f"{len(h1s)} H1, {len(h1_title)} ký tự", "Rút gọn H1 còn ≤ 70 ký tự, đưa từ khóa chính lên đầu",
        [(a.h1[0], quote(h1_title))] if a.h1 else [])

    # 25. số liệu có nguồn (tiêu chí 16 của aio_audit), chỉ liệt kê để người duyệt
    num = check_sourced_numbers(a)
    add(25, "Số liệu có chủ thể và nguồn (tiêu chí 16, người duyệt)", "Đạt" if num["pass"] else "Cần người duyệt",
        num["evidence"], num["fix"], [(h["line"], h["quote"]) for h in num["hits"]])

    if not nodes:
        add(26, "Schema FAQ khớp nguyên văn bài", "N/A", "Không có JSON-LD nên chưa đối chiếu Q/A")
    elif not faq and not schema_faq:
        add(26, "Schema FAQ khớp nguyên văn bài", "N/A", "Không có mục FAQ và không có FAQPage")
    else:
        faq_hits = [(f["line"], quote(f["q"])) for f, s in zip(faq, schema_faq)
                    if _norm(f["q"]) != _norm(s["q"]) or _norm(f["a"]) != _norm(s["a"])]
        add(26, "Schema FAQ khớp nguyên văn bài", "Chưa đạt" if mismatch else "Đạt",
            f"lệch: {mismatch}" if mismatch else f"{len(faq)} câu FAQ trùng nguyên văn",
            "Sinh lại bằng faq_schema() sau khi sửa FAQ", faq_hits)

    scored = [i for i in items if i["status"] in ("Đạt", "Chưa đạt", "Một phần")]
    passed = sum(1 for i in scored if i["status"] == "Đạt")
    return {"keyword": kw, "words": words, "score": f"{passed}/{len(scored)}", "score_percent": round(passed / len(scored) * 100, 1) if scored else 0,
            "required_failed": [i["id"] for i in items if i["required"] and i["status"] in ("Chưa đạt", "Một phần")],
            "complete": not any(i["required"] and i["status"] != "Đạt" for i in items), "items": items}


def faq_schema(markdown: str, url: str = "", site_name: str = "", image: str = "") -> str:
    """JSON-LD Article + FAQPage từ frontmatter và mục FAQ (nguyên văn) của bài."""
    a = as_article(markdown)
    fm = a.fm
    iso = ""
    for key in ("updated", "published"):
        try:
            iso = datetime.strptime(fm.get(key, ""), "%d/%m/%Y").date().isoformat()
            break
        except (ValueError, TypeError):
            continue
    article = {"@type": "Article", "headline": a.h1[2] if a.h1 else fm.get("meta_title", ""),
               "description": fm.get("meta_description", ""), "inLanguage": "vi-VN"}
    if fm.get("author"):
        article["author"] = {"@type": "Person", "name": fm["author"]}
    if site_name:
        article["publisher"] = {"@type": "Organization", "name": site_name}
    if iso:
        article["datePublished"] = article["dateModified"] = iso
    if url:
        article["mainEntityOfPage"] = url
    if image:
        article["image"] = image
    article = {k: v for k, v in article.items() if v}
    graph = [article]
    faq = a.faq()
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    js = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{js}\n</script>'
