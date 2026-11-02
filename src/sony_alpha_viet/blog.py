"""Blog/doc mode tools: slugify, word count, prose term lookup, style lint, SEO audit, FAQ schema."""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

# Read skill resources at runtime
def _get_skill_root() -> Path:
    """Locate skill dir relative to package root (repo root = parent of src)."""
    return Path(__file__).resolve().parents[2] / "skills" / "sony-alpha-viet"

def _load_glossary_vi() -> dict:
    """Load glossary-vi.md and parse markdown table: returns {en.lower(): {en, jp, menu, prose, note}}."""
    glossary_file = _get_skill_root() / "references" / "glossary-vi.md"
    if not glossary_file.exists():
        return {}

    content = glossary_file.read_text(encoding="utf-8")
    result = {}

    # Parse markdown tables: line with | separators after ## sections
    in_table = False
    for line in content.split("\n"):
        if line.startswith("##"):
            in_table = True
            continue
        if not line.startswith("|"):
            in_table = False
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

def count_words(text: str) -> int:
    """Whitespace-based word count, excluding markdown table rows, code fences, frontmatter."""
    # Remove frontmatter (--- ... ---)
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    # Remove code fences
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove markdown table rows (lines starting with |)
    lines = [l for l in text.split("\n") if not l.strip().startswith("|")]
    text = "\n".join(lines)
    # Count words
    return len(text.split())

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


def style_lint(text: str) -> dict:
    """Lint for style issues: AI-sounding phrases, passive voice, sentence length, etc."""
    issues = []
    ai_phrases = _load_ai_sounding_phrases()

    # Check for AI-sounding phrases
    for phrase in ai_phrases:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        for match in pattern.finditer(text):
            line_no = text[:match.start()].count("\n") + 1
            issues.append({
                "type": "ai_sounding",
                "match": phrase,
                "line": line_no,
                "hint": f"Tránh cụm: {phrase}"
            })

    # Check for passive voice: "được ... bởi"
    for match in re.finditer(r"được\s+\w+\s+bởi", text):
        line_no = text[:match.start()].count("\n") + 1
        issues.append({
            "type": "passive",
            "match": match.group(0),
            "line": line_no,
            "hint": "Dùng chủ động thay vì bị động"
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

    # Check doubled words
    for match in re.finditer(r"\b(\w+)\s+\1\b", text):
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


# ---------------- article parsing ----------------
def _frontmatter(md: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body). Values in quotes or [lists] are parsed loosely."""
    m = re.match(r"---\n(.*?)\n---\n", md, re.DOTALL)
    if not m:
        return {}, md
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            v = re.sub(r"\s+#.*$", "", v.strip())
            if v.startswith("["):
                fm[k.strip()] = [x.strip().strip('"\'') for x in v.strip("[]").split(",") if x.strip()]
            else:
                fm[k.strip()] = v.strip('"\'')
    return fm, md[m.end():]


def _strip_code(md: str) -> str:
    return re.sub(r"```.*?```", "", md, flags=re.DOTALL)


def _section(body: str, heading_rx: str) -> str:
    """Text of the H2 section whose title matches heading_rx (up to the next H2)."""
    m = re.search(r"^##\s+(?:" + heading_rx + r")\s*$", body, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^##\s", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


FAQ_HEADING = r"Câu hỏi thường gặp|FAQ|Hỏi đáp"


def _faq(body: str) -> list[dict]:
    """[{q, a}] from the FAQ section; answers keep every paragraph up to the next H3."""
    sec = _strip_code(_section(body, FAQ_HEADING))
    parts = re.split(r"^###\s+(.+?)\s*$", sec, flags=re.MULTILINE)
    out = []
    for i in range(1, len(parts) - 1, 2):
        a = re.sub(r"\s+", " ", parts[i + 1]).strip()
        out.append({"q": parts[i].strip(), "a": a})
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip().lower()


def _jsonld(md: str) -> list[dict]:
    blocks = re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", md, re.DOTALL)
    out = []
    for b in blocks:
        try:
            data = json.loads(b)
        except json.JSONDecodeError:
            out.append({"_error": "JSON không hợp lệ"})
            continue
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        out.extend(n for n in nodes if isinstance(n, dict))
    return out


# ---------------- SEO / AIO audit ----------------
REQUIRED = {1, 6, 8, 11, 15, 19, 21}


def seo_audit(markdown: str, primary_keyword: str = "", secondary_keywords: Optional[list[str]] = None) -> dict:
    """Chấm bài theo references/seo-aio-checklist.md. Mục không chấm bằng máy được → "Cần người duyệt"."""
    md = unicodedata.normalize("NFC", markdown)
    fm, body = _frontmatter(md)
    kw = (primary_keyword or fm.get("primary_keyword") or "").strip()
    kwl = kw.lower()
    prose = _strip_code(body)
    items = []

    def add(i, item, status, evidence="", fix=""):
        items.append({"id": i, "item": item, "status": status, "required": i in REQUIRED, "evidence": evidence, "fix": fix if status != "Đạt" else ""})

    h1s = re.findall(r"^#\s+(.+)$", prose, re.MULTILINE)
    h2s = re.findall(r"^##\s+(.+)$", prose, re.MULTILINE)
    title, desc, slug = fm.get("meta_title", ""), fm.get("meta_description", ""), fm.get("slug", "")
    first100 = " ".join(re.sub(r"[#*_>|`\[\]]", " ", prose).split()[:100]).lower()

    # 1. keyword placement
    if not kw:
        add(1, "Từ khóa chính ở H1, slug, 100 từ đầu, H2, meta description", "Chưa đạt", "Không có từ khóa chính", "Truyền primary_keyword hoặc khai báo trong frontmatter")
    else:
        where = {"H1": any(kwl in h.lower() for h in h1s), "slug": slugify(kw, 20) in slug,
                 "100 từ đầu": kwl in first100, "H2": any(kwl in h.lower() for h in h2s), "meta description": kwl in desc.lower()}
        miss = [k for k, v in where.items() if not v]
        add(1, "Từ khóa chính ở H1, slug, 100 từ đầu, H2, meta description", "Đạt" if not miss else "Chưa đạt",
            "; ".join(f"{k}={'có' if v else 'thiếu'}" for k, v in where.items()), "Thêm từ khóa vào: " + ", ".join(miss))

    # 2–4. meta + slug
    add(2, "Meta title 50–60 ký tự", "Đạt" if 50 <= len(title) <= 60 else ("Chưa đạt" if title else "Chưa đạt"),
        f"{len(title)} ký tự" if title else "Thiếu meta_title", "Viết lại meta title trong khoảng 50–60 ký tự, từ khóa ở nửa đầu")
    add(3, "Meta description 140–160 ký tự", "Đạt" if 140 <= len(desc) <= 160 else "Chưa đạt",
        f"{len(desc)} ký tự" if desc else "Thiếu meta_description", "Viết lại trong khoảng 140–160 ký tự, có lợi ích + hành động")
    slug_ok = bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)) and len(slug.split("-")) <= 6
    add(4, "Slug không dấu, gạch nối, ≤ 6 từ", "Đạt" if slug_ok else "Chưa đạt", f"'{slug}'", f"Gợi ý: {slugify(kw or (h1s[0] if h1s else ''))}")

    # 5. density = occurrences / words
    words = count_words(md)
    occ = len(re.findall(re.escape(kw), prose, re.IGNORECASE)) if kw else 0
    dens = occ / words * 100 if words else 0
    add(5, "Không nhồi từ khóa (≤ 1,5%)", "Đạt" if kw and dens <= 1.5 else ("N/A" if not kw else "Chưa đạt"),
        f"{occ} lần / {words} từ = {dens:.2f}%".replace(".", ","), "Giảm số lần lặp cụm từ khóa chính, dùng biến thể")

    # 6. TL;DR
    m = re.search(r"\*\*TL;DR:?\*\*:?\s*(.+)", prose)
    n = len(m.group(1).split()) if m else 0
    add(6, "TL;DR 40–70 từ ngay sau H1", "Đạt" if 40 <= n <= 70 else "Chưa đạt", f"{n} từ" if m else "Không có **TL;DR:**",
        "Thêm/sửa TL;DR 40–70 từ trả lời thẳng câu hỏi chính")

    # 7. headings
    levels = [len(x) for x in re.findall(r"^(#{1,6})\s", prose, re.MULTILINE)]
    jumps = [f"H{a}→H{b}" for a, b in zip(levels, levels[1:]) if b > a + 1]
    add(7, "Một H1; heading không nhảy cấp", "Đạt" if len(h1s) == 1 and not jumps else "Chưa đạt",
        f"{len(h1s)} H1" + (f"; nhảy cấp: {', '.join(jumps)}" if jumps else ""), "Giữ đúng một H1, không bỏ cấp heading")

    # 8. structure
    table = bool(re.search(r"^\|.+\|\s*$\n^\|[-:| ]+\|\s*$", prose, re.MULTILINE))
    lst = bool(re.search(r"^\s*(?:[-*+]|\d+\.)\s+\S", prose, re.MULTILINE))
    add(8, "Có bảng, checklist hoặc danh sách", "Đạt" if table or lst else "Chưa đạt", f"bảng={'có' if table else 'không'}; danh sách={'có' if lst else 'không'}",
        "Thêm bảng so sánh hoặc danh sách các bước")

    # 9. paragraph length
    paras = [p for p in re.split(r"\n\s*\n", prose) if p.strip() and not re.match(r"\s*(?:#|\||[-*+]\s|\d+\.\s|>)", p)]
    long_p = [p for p in paras if len(re.findall(r"[.!?](?:\s|$)", p)) > 4]
    add(9, "Đoạn ≤ 4 câu; mỗi H2 mở bằng câu trả lời ngắn", "Đạt" if not long_p else "Một phần",
        f"{len(long_p)} đoạn > 4 câu", "Tách đoạn dài; mở mỗi H2 bằng câu trả lời 1–2 câu")
    add(10, "Kết luận có hành động cụ thể", "Cần người duyệt", "Có H2 kết luận" if any(re.search(r"kết luận|tóm lại|nên chọn", h, re.I) for h in h2s) else "Không thấy H2 kết luận",
        "Kết thúc bằng khuyến nghị theo nhóm người dùng + bước tiếp theo")

    # 11. FAQ
    faq = _faq(body)
    lens = [len(f["a"].split()) for f in faq]
    bad_ctx = [f["q"] for f in faq if re.search(r"như đã nói|ở trên|phía trên", f["a"], re.I)]
    ok = 3 <= len(faq) <= 6 and all(40 <= x <= 70 for x in lens) and not bad_ctx
    add(11, "FAQ 3–6 câu, mỗi câu trả lời 40–70 từ, tự đứng được", "Đạt" if ok else ("Chưa đạt" if not faq else "Một phần"),
        f"{len(faq)} câu; số từ={lens}" + (f"; phụ thuộc ngữ cảnh: {bad_ctx}" if bad_ctx else ""), "Chỉnh số câu hỏi/độ dài; bỏ tham chiếu 'như đã nói ở trên'")
    add(12, "Có định nghĩa một câu cho khái niệm chính", "Đạt" if re.search(r"\b(?:là|được hiểu là)\b", prose) else "Cần người duyệt", "", "Thêm câu 'X là …' cho khái niệm chính")
    add(13, "Câu số liệu nêu rõ chủ thể và đơn vị", "Cần người duyệt", "", "Kiểm các câu có số: tránh 'nó', 'máy này'")
    add(14, "Có trải nghiệm/bối cảnh riêng (Việt Nam)", "Cần người duyệt", "", "Thêm ví dụ thực tế: địa điểm, giá, dịch vụ, thói quen chụp")

    # 15. unverified
    nv = len(re.findall(r"\[cần xác minh[^\]]*\]", prose))
    add(15, "Không có thông số/giá chưa kiểm chứng", "Đạt" if nv == 0 else "Chưa đạt", f"{nv} chỗ [cần xác minh]", "Đối chiếu nguồn chính thức rồi bỏ đánh dấu")

    # 16–17. links (outside code/JSON-LD)
    ext = sorted(set(re.findall(r"https?://[^\s)\]>\"']+", prose)))
    internal = re.findall(r"\[link nội bộ:[^\]]*\]", prose, re.I)
    rel = re.findall(r"\]\((/[^)]+)\)", prose)
    add(16, "Link ngoài 1–3 nguồn uy tín", "Đạt" if 1 <= len(ext) <= 3 else ("Một phần" if ext else "Chưa đạt"), f"{len(ext)} link: " + ", ".join(ext[:5]),
        "Giữ 1–3 nguồn mạnh nhất (ưu tiên trang Sony chính thức)")
    n_int = len(internal) + len(rel)
    add(17, "Link nội bộ 2–5", "Đạt" if 2 <= len(rel) <= 5 else ("Một phần" if n_int else "Chưa đạt"),
        f"{len(rel)} URL thật, {len(internal)} placeholder", "Thay placeholder [link nội bộ: …] bằng URL thật")
    add(18, "Tác giả và ngày cập nhật", "Đạt" if fm.get("author") and fm.get("updated") else "Chưa đạt",
        f"author={fm.get('author', '')}; updated={fm.get('updated', '')}", "Thêm author, updated vào frontmatter")

    # 19. JSON-LD
    nodes = _jsonld(md)
    types = {n.get("@type") for n in nodes}
    errs = [n["_error"] for n in nodes if "_error" in n]
    schema_faq = []
    for n in nodes:
        if n.get("@type") == "FAQPage":
            schema_faq = [{"q": e.get("name", ""), "a": (e.get("acceptedAnswer") or {}).get("text", "")} for e in n.get("mainEntity", [])]
    mismatch = [f["q"] for f, s in zip(faq, schema_faq) if _norm(f["q"]) != _norm(s["q"]) or _norm(f["a"]) != _norm(s["a"])]
    if len(faq) != len(schema_faq):
        mismatch.append(f"số câu: bài {len(faq)} / Schema {len(schema_faq)}")
    need_howto = bool(re.search(r"hướng dẫn|cách cài|từng bước", h1s[0] if h1s else "", re.I))
    ok19 = not errs and "Article" in types and "FAQPage" in types and not mismatch and (not need_howto or "HowTo" in types)
    add(19, "JSON-LD Article + FAQPage (+ HowTo nếu hướng dẫn), FAQ trùng nguyên văn", "Đạt" if ok19 else ("Chưa đạt" if not nodes else "Một phần"),
        f"types={sorted(t for t in types if t)}" + (f"; lỗi={errs}" if errs else "") + (f"; lệch FAQ={mismatch}" if mismatch else "") + ("; thiếu HowTo" if need_howto and "HowTo" not in types else ""),
        "Sinh lại bằng faq_schema() sau khi chốt FAQ")

    # 20. images
    imgs = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", prose)
    no_alt = [src for alt, src in imgs if not alt.strip()]
    add(20, "Ảnh có alt text", "N/A" if not imgs else ("Đạt" if not no_alt else "Chưa đạt"), f"{len(imgs)} ảnh, {len(no_alt)} thiếu alt", "Thêm alt mô tả tiếng Việt")

    # 21–22. terminology + style
    lint = style_lint(prose)["issues"]
    term = [i for i in lint if i["type"] == "terminology"]
    style = [i for i in lint if i["type"] not in ("terminology", "verify_markers")]
    add(21, "Thuật ngữ đúng glossary", "Đạt" if not term else "Chưa đạt", "; ".join(f"dòng {i['line']}: {i['match']}" for i in term[:5]), "; ".join(i["hint"] for i in term[:3]))
    add(22, "Không văn dịch máy / cụm AI-sounding", "Đạt" if not style else "Một phần", f"{len(style)} vấn đề: " + "; ".join(f"{i['type']}:{i['match'][:30]}" for i in style[:5]),
        "Sửa theo style_lint()")
    add(23, "Không khuyến nghị y tế/tài chính/pháp lý thiếu căn cứ", "Cần người duyệt", "", "")

    scored = [i for i in items if i["status"] in ("Đạt", "Chưa đạt", "Một phần")]
    passed = sum(1 for i in scored if i["status"] == "Đạt")
    return {"keyword": kw, "words": words, "score": f"{passed}/{len(scored)}", "score_percent": round(passed / len(scored) * 100, 1) if scored else 0,
            "required_failed": [i["id"] for i in items if i["required"] and i["status"] in ("Chưa đạt", "Một phần")],
            "complete": not any(i["required"] and i["status"] != "Đạt" for i in items), "items": items}


def faq_schema(markdown: str, url: str = "", site_name: str = "", image: str = "") -> str:
    """JSON-LD Article + FAQPage từ frontmatter và mục FAQ (nguyên văn) của bài."""
    md = unicodedata.normalize("NFC", markdown)
    fm, body = _frontmatter(md)
    h1 = re.search(r"^#\s+(.+)$", _strip_code(body), re.MULTILINE)
    iso = ""
    for key in ("updated", "published"):
        try:
            iso = datetime.strptime(fm.get(key, ""), "%d/%m/%Y").date().isoformat()
            break
        except ValueError:
            continue
    article = {"@type": "Article", "headline": h1.group(1).strip() if h1 else fm.get("meta_title", ""),
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
    faq = _faq(body)
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    js = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{js}\n</script>'
