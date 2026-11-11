"""
aio_audit.py - Chấm AIO-first: 13 tiêu chí máy kiểm được (11-19, 21-23, 33) trong seo-aio-checklist.md.
Tiêu chí 20 (PAA) kiểm tay bằng paa_generator. Mọi check nhận markdown (str) hoặc Article (xem _doc.py).

Cách dùng:
  aio_audit(text, primary_keyword, article_type="review", today="") -> dict (aio_score, items, table)
Article types: review (default), comparison, howto. Không cần internet.
"""

import re

from ._doc import (BULLET_RX, HEADING_RX, SOURCE_WORD_RX, as_article, as_date, band, finding, fold,
                   quote, stamps, tldr)

FAQ_RX = r"^(faq|cau hoi thuong gap|hoi dap)\b"
SKIP_H2_RX = r"^(faq|cau hoi thuong gap|hoi dap|nguon|tai lieu|key takeaways|tom tat trong tam|tu audit|ket luan)"
OPENER_RX = r"^(trong phan nay|hay cung|o phan nay|bai viet nay)"
FORBIDDEN_REF_RX = r"xem o tren|nhu da noi|da de cap|nhu tren|xem phan tren|nhu o tren"
DEF_RX = re.compile(r"(?:^|[.!?]\s+)([^.!?|#]{2,60}?)\s+(?:la|nghia la|tuc la|duoc goi la)\s+[^.!?]{6,}[.!?]")
DEF_SKIP_FIRST = {"day", "do", "no", "dieu", "viec", "neu", "khi", "minh", "ban", "toi", "cai", "noi", "chung"}
NUM_RX = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?\s?(?:mp|fps|shots?|lens|mm|stops?|ev|trieu|%|kg|g|inch|ms|giay|phut|gio|lan|vnd|usd|k)(?!\w)")
MODEL_RX = re.compile(r"\b(?:zv-?e10(?: ii)?|a6\d{3}|a7\s?(?:iv|c|s\s?iii|r\s?v)|a9\s?(?:iii|ii)|ilce-?\w+|fx\d+)\b")
SPEC_RX = re.compile(r"\d+\s?mp\b|full-?frame|\bibis\b|eye af|ngam e|e-mount")
VN_RX = r"viet nam|hcm|sai gon|ha noi|da nang|nong am"
TAKEAWAY_RX = r"key takeaways|diem chinh|tom tat trong tam"
PRO_RX = r"(?:uu diem|diem manh|pros)\b"
CON_RX = r"(?:nhuoc diem|diem yeu|han che|cons|can nhac)\b"
BANNED = [
    ("Hãy cùng khám phá", r"hay cung kham pha"),
    ("đưa trải nghiệm lên tầm cao mới", r"dua trai nghiem len tam cao moi"),
    ("tối ưu hóa trải nghiệm", r"toi uu hoa trai nghiem"),
    ("không chỉ ... mà còn", r"khong chi\b.{0,60}\bma con\b"),
    ("vô cùng quan trọng", r"vo cung quan trong"),
]


def check_h2_self_contained(text) -> dict:
    """Criterion 12: H2 nội dung mở bằng câu trả lời. Lỗi khi: mở bằng văn sáo rỗng, mở bằng bảng/danh sách/ảnh
    chưa có câu dẫn, hoặc câu mở chỉ là câu hỏi. Bỏ qua FAQ, Key Takeaways, Nguồn tham khảo, Kết luận."""
    a = as_article(text)
    name = "H2 mở bằng câu tự đứng"
    secs = [s for s in a.h2_sections() if not re.search(SKIP_H2_RX, fold(s[1]))]
    if not secs:
        return finding(12, name, False, "Không có H2 nội dung", "Thêm ít nhất 3 H2 nội dung ngay dưới TL;DR")
    blocks = a.blocks()
    issues = []  # {line, title, quote, reason}: quote là câu mở của H2 lỗi
    for ln, title, end in secs:
        body = [b for b in blocks if ln < b[0][0] <= end]
        if not body:
            issues.append({"line": ln, "title": title, "quote": f"## {title}", "reason": "mục trống, chưa có câu mở"})
            continue
        first_line = body[0][0][1]
        text0 = " ".join(t.strip() for _, t in body[0])
        if first_line.lstrip().startswith(("|", "![")) or BULLET_RX.match(first_line):
            issues.append({"line": body[0][0][0], "title": title, "quote": quote(first_line),
                           "reason": "mở bằng bảng, danh sách hoặc ảnh, chưa có câu dẫn"})
            continue
        m = re.match(r"(.+?[.!?])(?:\s|$)", text0)
        sent = (m.group(1) if m else text0).strip()
        if re.search(OPENER_RX, fold(text0)):
            issues.append({"line": body[0][0][0], "title": title, "quote": quote(sent), "reason": "mở bằng văn sáo rỗng"})
        elif sent.endswith("?") and sent == text0.strip():
            issues.append({"line": body[0][0][0], "title": title, "quote": quote(sent), "reason": "câu mở chỉ là câu hỏi"})
    if not issues:
        return finding(12, name, True, f"{len(secs)} H2 nội dung mở bằng câu trả lời")
    shown = "; ".join(f"{i['title']} (dòng {i['line']}, {i['reason']})" for i in issues)
    return finding(12, name, False, f"H2 lỗi: {shown}",
                   "Mở mỗi H2 bằng 1-2 câu trả lời thẳng; bỏ 'Trong phần này...', đặt câu dẫn trước bảng/danh sách, "
                   "viết câu hỏi thành câu trả lời",
                   [(i["line"], i["quote"]) for i in issues])


def has_tldr(text) -> dict:
    """Criterion 11: TL;DR có nhãn, 40-70 từ, ngay dưới H1. Bullet hoặc đoạn đều đếm như nhau."""
    a = as_article(text)
    name = "TL;DR 40-70 từ"
    t = tldr(a)
    if not t["line"]:
        return finding(11, name, False, "Không tìm thấy H1", "Thêm H1 với từ khóa chính, TL;DR ngay dưới")
    if not t["labelled"]:
        return finding(11, name, False, f"Không có nhãn TL;DR; đoạn đầu {t['words']} từ",
                       "Thêm nhãn **TL;DR:** và 40-70 từ ngay dưới H1", [(t["line"], t["quote"])])
    if not 40 <= t["words"] <= 70:
        return finding(11, name, False, f"TL;DR {t['words']} từ ({t['form']}), cần 40-70",
                       "Rút gọn hoặc mở rộng TL;DR về 40-70 từ", [(t["line"], t["quote"])])
    return finding(11, name, True, f"TL;DR {t['words']} từ ({t['form']})")


def check_definition(text) -> dict:
    """Criterion 13: có ít nhất một định nghĩa dạng 'X là ...'. Chưa kiểm được mọi thuật ngữ."""
    a = as_article(text)
    name = "Định nghĩa 1 câu"
    for i, ln in enumerate(a.lines):
        if not ln.strip() or HEADING_RX.match(ln) or ln.lstrip().startswith("|"):
            continue
        for m in DEF_RX.finditer(fold(ln)):
            words = m.group(1).split()
            if words and len(words) <= 6 and words[0] not in DEF_SKIP_FIRST:
                return finding(13, name, True, f"Có định nghĩa ở dòng {i + 1}: {quote(ln, 60)}")
    return finding(13, name, False, "Không có câu dạng 'X là ...'",
                   "Thêm ngay dưới H2 đầu tiên một định nghĩa 1 câu cho thuật ngữ chính, ví dụ 'Ngàm E là ...'")


def check_faq(text) -> dict:
    """Criterion 14: mục FAQ 3-6 câu, mỗi đáp 40-70 từ, không dùng 'xem ở trên'/'như đã nói'."""
    a = as_article(text)
    name = "FAQ 3-6 câu tự đứng"
    sec = a.section(FAQ_RX)
    if not sec:
        return finding(14, name, False, "Không có mục FAQ",
                       "Thêm mục '## FAQ' ngay trước Key Takeaways (cuối bài) với 3-6 câu hỏi, mỗi đáp 40-70 từ")
    qs = a.faq()
    if not 3 <= len(qs) <= 6:
        return finding(14, name, False, f"FAQ có {len(qs)} câu, cần 3-6",
                       "Chỉnh còn 3-6 câu hỏi người dùng thật sự gõ", [(sec[0], a.lines[sec[0] - 1])])
    hits = []
    for q in qs:
        ref = re.search(FORBIDDEN_REF_RX, fold(q["a"]))
        if not 40 <= q["words"] <= 70:
            hits.append((q["line"], f"{q['q']} ({q['words']} từ)"))
        elif ref:
            hits.append((q["line"], f"{q['q']} (cụm '{ref.group(0)}')"))
    if hits:
        return finding(14, name, False, f"FAQ lỗi: {hits[0][1]}",
                       "Viết lại đáp 40-70 từ, tự đứng, không dùng 'xem ở trên'/'như đã nói'", hits)
    return finding(14, name, True, f"FAQ {len(qs)} câu, mỗi đáp 40-70 từ, tự đứng")


def check_table(text) -> dict:
    """Criterion 15: bảng ≥3 cột với ≥2 dòng dữ liệu, hoặc checklist ≥3 mục."""
    a = as_article(text)
    name = "Bảng so sánh hoặc checklist"
    tabs = a.tables()
    good = [t for t in tabs if t["cols"] >= 3 and t["rows"] >= 2]
    if good:
        t = good[0]
        return finding(15, name, True, f"Bảng {t['cols']} cột, {t['rows']} dòng dữ liệu (dòng {t['line']})")
    tasks = a.task_items()
    if len(tasks) >= 3:
        return finding(15, name, True, f"Checklist {len(tasks)} mục (dòng {tasks[0][0]})")
    return finding(15, name, False, "Không có bảng ≥3 cột và ≥2 dòng dữ liệu, hoặc checklist ≥3 mục",
                   "Thêm vào H2 so sánh một bảng ≥3 cột (tiêu chí × sản phẩm) với ≥2 dòng dữ liệu, hoặc checklist ≥3 mục",
                   [(t["line"], " | ".join(t["header"])) for t in tabs])


YEAR_RX = re.compile(r"\b(?:19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{1,2}[/-]\d{4}\b")
LENS_RX = re.compile(r"\b\d+(?:[.,]\d+)?\s?mm\b")


def _figures(line: str) -> set:
    """Số liệu có đơn vị trong dòng (đã fold), bỏ tên model, tiêu cự ống kính, năm và ngày."""
    s = fold(line)
    for rx in (MODEL_RX, LENS_RX, YEAR_RX):
        s = rx.sub(" ", s)
    return {m.group(0).replace(",", ".").replace(" ", "") for m in NUM_RX.finditer(s)}


def _caption_lines(src: list, i: int, j: int) -> list:
    """Dòng không trống gần nhất ngay trên và ngay dưới khối bảng [i, j) (chú thích hoặc đoạn dẫn)."""
    up = next((src[k] for k in range(i - 1, -1, -1) if src[k].strip()), "")
    down = next((src[k] for k in range(j, len(src)) if src[k].strip()), "")
    return [up, down]


def check_sourced_numbers(text) -> dict:
    """Criterion 16: số liệu có chủ thể và nguồn. Chỉ là việc cần người duyệt, không bao giờ fail.
    Số liệu coi là có nguồn khi: cùng số liệu xuất hiện ở dòng/hàng có dấu nguồn; hoặc bài có mục
    'Nguồn tham khảo' và bảng chứa số liệu có chú thích/đoạn dẫn nêu nguồn."""
    a = as_article(text)
    name = "Số liệu có chủ thể và nguồn"
    src = a.lines
    has_ref = any("nguon tham khao" in fold(t) for _, _, t in a.headings)
    marked = [bool(SOURCE_WORD_RX.search(fold(ln))) for ln in src]
    marked_figs = set()
    for ln, ok in zip(src, marked):
        if ok:
            marked_figs |= _figures(ln)
    cited, i = set(), 0
    while i < len(src):
        if not src[i].lstrip().startswith("|"):
            i += 1
            continue
        j = i
        while j < len(src) and src[j].lstrip().startswith("|"):
            j += 1
        if has_ref and any(SOURCE_WORD_RX.search(fold(c)) for c in _caption_lines(src, i, j)):
            cited.update(range(i, j))
        i = j
    hits, total = [], 0
    for k, ln in enumerate(src):
        figs = _figures(ln)
        if not figs:
            continue
        total += 1
        if marked[k] or k in cited or figs <= marked_figs:
            continue
        hits.append((k + 1, quote(ln)))
    if not total:
        return finding(16, name, True, "Không có số liệu cần nguồn")
    if not hits:
        return finding(16, name, True, f"{total} dòng có số liệu, đều có nguồn")
    where = ", ".join(str(ln) for ln, _ in hits)
    return finding(16, name, False, f"Cần người duyệt: số liệu chưa thấy nguồn ở dòng {where}",
                   "Ghi chủ thể và nguồn ngay cạnh số liệu, ví dụ '(nguồn: Sony official, 2026)'", hits, manual=True)


def check_placeholder(text) -> dict:
    """Criterion 17: không còn [cần xác minh] (không phân biệt hoa thường, dấu)."""
    a = as_article(text)
    name = "Không placeholder [cần xác minh]"
    hits = [(ln, quote(raw)) for ln, raw in a.grep(r"\[can xac minh\]")]
    if not hits:
        return finding(17, name, True, "Không còn [cần xác minh]")
    lines = ", ".join(str(ln) for ln, _ in hits)
    return finding(17, name, False, f"Còn {len(hits)} placeholder [cần xác minh] ở dòng {lines}",
                   "Kiểm tra trên trang Sony official, thay [cần xác minh] bằng số liệu đã kiểm chứng kèm nguồn; "
                   "không xóa placeholder khi chưa kiểm chứng", hits)


def check_pros_cons(text) -> dict:
    """Criterion 18: có khối Ưu điểm và khối Nhược điểm, mỗi khối ≥2 bullet (tiêu đề hoặc nhãn đứng đầu dòng)."""
    a = as_article(text)
    name = "Ưu/nhược điểm"
    groups = {"pro": [], "con": []}
    for i, ln in enumerate(a.lines):
        f = re.sub(r"^(?:#{1,6}\s+|[-*+]\s+|\*\*|__)+", "", fold(ln).strip())
        kind = "pro" if re.match(PRO_RX, f) else "con" if re.match(CON_RX, f) else None
        if not kind:
            continue
        n, j = 0, i + 1
        while j < len(a.lines):
            if not a.lines[j].strip():
                j += 1
            elif BULLET_RX.match(a.lines[j]):
                n += 1
                j += 1
            else:
                break
        if n >= 2:
            groups[kind].append((i + 1, quote(ln, 60)))
    if groups["pro"] and groups["con"]:
        return finding(18, name, True, f"Có ưu điểm (dòng {groups['pro'][0][0]}) và nhược điểm (dòng {groups['con'][0][0]})")
    missing = "ưu điểm" if not groups["pro"] else "nhược điểm"
    return finding(18, name, False, f"Thiếu khối {missing} (tiêu đề hoặc nhãn + ≥2 bullet)",
                   "Thêm dưới H2 đánh giá hai khối 'Ưu điểm' và 'Nhược điểm', mỗi khối ≥2 bullet; "
                   "nhược điểm nêu bối cảnh và giải pháp")


def check_vn_context(text, article_type: str = "review") -> dict:
    """Criterion 19: có bối cảnh Việt Nam (khí hậu, thành phố, dịch vụ). Howto không yêu cầu."""
    a = as_article(text)
    name = "Ví dụ thực tế VN"
    if article_type == "howto":
        return finding(19, name, True, "Howto - không yêu cầu")
    hits = a.grep(VN_RX)
    if hits:
        return finding(19, name, True, f"Có bối cảnh VN (dòng {hits[0][0]})")
    return finding(19, name, False, "Thiếu bối cảnh VN (Việt Nam, HCM, Hà Nội, khí hậu nóng ẩm)",
                   "Thêm một đoạn ví dụ thực tế Việt Nam (địa điểm, khí hậu, giá, dịch vụ) trong H2 thân bài")


def check_ai_sounding(text) -> dict:
    """Criterion 21: không có cụm sáo rỗng AI-sounding."""
    a = as_article(text)
    name = "Không AI-sounding"
    found, hits = [], []
    for label, pat in BANNED:
        for ln, raw in a.grep(pat):
            if label not in found:
                found.append(label)
            hits.append((ln, quote(raw)))
    if not hits:
        return finding(21, name, True, "Không có cụm AI-sounding")
    return finding(21, name, False, f"Có cụm AI-sounding: {', '.join(found)}",
                   "Bỏ cụm sáo rỗng, viết trực tiếp", hits)


def check_entity(text, keyword: str = "") -> dict:
    """Criterion 22: có từ khóa chính (nếu truyền) và entity rõ: model Sony, hoặc Sony + thông số."""
    a = as_article(text)
    name = "Entity rõ ràng"
    prose = fold(a.prose)
    kw = fold(keyword or "").strip()
    if kw and kw not in prose:
        return finding(22, name, False, f"Thiếu từ khóa chính '{keyword}'",
                       f"Thêm '{keyword}' vào H1, 100 từ đầu và 1 H2")
    model = MODEL_RX.search(prose)
    if model:
        return finding(22, name, True, f"Có model Sony: {model.group(0)}")
    if "sony" in prose and SPEC_RX.search(prose):
        return finding(22, name, True, "Có Sony + thông số (MP, full-frame, IBIS, Eye AF, ngàm E)")
    return finding(22, name, False, "Thiếu entity rõ ràng",
                   "Trong đoạn mở đầu, thêm model code của máy (ví dụ [model]) hoặc ghi Sony kèm thông số (full-frame, MP, IBIS)")


def check_freshness(text, today="") -> dict:
    """Criterion 23: có mốc 'Cập nhật MM/YYYY' hoặc ngày, và mốc mới nhất trong vòng 365 ngày tính tới today."""
    a = as_article(text)
    d = as_date(today)
    name = "Cập nhật"
    fix = f"Thêm dòng 'Cập nhật {d:%m/%Y}: [nội dung cập nhật]' ngay dưới TL;DR"
    st = stamps(a)
    if not st:
        return finding(23, name, False, "Không có dòng 'Cập nhật MM/YYYY'", fix)
    latest = max(st, key=lambda s: s["date"])
    if (d - latest["date"]).days > 365:
        return finding(23, name, False, f"Mốc cập nhật mới nhất {latest['date']:%m/%Y} đã quá 365 ngày",
                       fix, [(latest["line"], latest["quote"])])
    return finding(23, name, True, f"Mốc cập nhật {latest['date']:%m/%Y}, trong 365 ngày")


def check_takeaways(text) -> dict:
    """Criterion 33: mục Key Takeaways có 3-5 bullet."""
    a = as_article(text)
    name = "Key Takeaways 3-5 bullet"
    for ln, lv, title in a.headings:
        if lv in (2, 3) and re.search(TAKEAWAY_RX, fold(title)):
            end = a.end_of(ln, lv)
            n = sum(1 for i in range(ln, end) if BULLET_RX.match(a.lines[i]))
            if 3 <= n <= 5:
                return finding(33, name, True, f"{n} bullet tóm tắt (dòng {ln})")
            return finding(33, name, False, f"Key Takeaways có {n} bullet, cần 3-5",
                           "Viết 3-5 bullet tóm gọn cho người đọc lướt", [(ln, title)])
    return finding(33, name, False, "Không có mục Key Takeaways",
                   "Thêm '## Key Takeaways' với 3-5 bullet ở cuối bài")


def aio_audit(text, primary_keyword: str = "", article_type: str = "review", today="") -> dict:
    """
    Tool MCP: aio_audit
    Input: text (markdown bài viết), primary_keyword, article_type ("review"|"comparison"|"howto"),
           today (YYYY-MM-DD hoặc '' = hôm nay, dùng cho tiêu chí 23)
    Output: aio_score (0-100), verdict (Đạt/Cần sửa/Thấp), items (theo tiêu chí), table (hiển thị), manual
    """
    a = as_article(text)
    d = as_date(today)
    items = [
        has_tldr(a),
        check_h2_self_contained(a),
        check_definition(a),
        check_faq(a),
        check_table(a),
        check_sourced_numbers(a),
        check_placeholder(a),
        check_pros_cons(a),
        check_vn_context(a, article_type),
        check_ai_sounding(a),
        check_entity(a, primary_keyword),
        check_freshness(a, d),
        check_takeaways(a),
    ]
    items.sort(key=lambda r: r["criterion"])
    # Mục cần người duyệt không nằm trong mẫu số điểm
    checked = [r for r in items if r["pass"] or not r.get("manual")]
    passed = sum(1 for r in checked if r["pass"])
    score = int(passed / len(checked) * 100) if checked else 0

    table = [
        {
            "Mục": f"{r['criterion']} {r['item']}",
            "Kết quả": "✅ Đạt" if r["pass"] else ("⚠ Cần người duyệt" if r.get("manual") else "❌ Chưa"),
            "Bằng chứng": r["evidence"][:100],
            "Cách sửa": r["fix"],
        }
        for r in items
    ]
    manual = [{"criterion": 20, "item": "Bao quát câu hỏi PAA", "note": "Đối chiếu paa_generator; máy không kiểm được"}]
    manual += [{"criterion": r["criterion"], "item": r["item"], "note": r["evidence"]}
               for r in items if r.get("manual")]
    return {
        "aio_score": score,
        "passed": f"{passed}/{len(checked)}",
        "verdict": band(score),
        "items": items,
        "table": table,
        "manual": manual,
        "primary_keyword": primary_keyword,
        "article_type": article_type,
        "today": d.isoformat(),
    }
