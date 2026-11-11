"""
audit.py - Tool MCP blog_audit: chấm bài một lượt theo 40 tiêu chí (chỉ đọc).

Gom kết quả aio_audit, brand_voice_checker, seo_audit, citation_checker, freshness_check
theo số tiêu chí của references/seo-aio-checklist.md (1–40). Mỗi tiêu chí có đúng một trạng thái:
pass, fail, manual (người duyệt), not_checked (chưa có bộ kiểm), na (bỏ qua, có lý do).
Nguồn máy ưu tiên nhất quyết định; máy luôn thắng người duyệt. Không ghi file, không đổi trạng thái.
"""

from typing import Optional

from ._doc import as_article, as_date, band, finding, fold, links, quote
from .aio_audit import aio_audit
from .brand_voice_checker import brand_voice_checker
from .citation_checker import citation_checker
from .freshness_check import freshness_check

NAMES = {
    1: "Từ khóa chính", 2: "Meta title & description", 3: "Cấu trúc heading", 4: "Mật độ từ khóa",
    5: "Liên kết trong & ngoài", 6: "Ảnh có alt text", 7: "Đoạn ngắn, dễ đọc", 8: "Slug chuẩn SEO",
    9: "Ngày xuất bản & cập nhật", 10: "Tác giả & E-E-A-T", 11: "TL;DR 40–70 từ",
    12: "H2 mở bằng câu trả lời", 13: "Định nghĩa một câu", 14: "FAQ 3–6 câu tự đứng",
    15: "Bảng so sánh hoặc checklist", 16: "Số liệu có chủ thể và nguồn", 17: "Không còn placeholder",
    18: "Ưu/nhược điểm", 19: "Bối cảnh Việt Nam", 20: "Bao quát câu hỏi PAA", 21: "Không văn phong AI-sounding",
    22: "Thực thể (entity) rõ ràng", 23: "Dòng cập nhật thời gian", 24: "Video / đa phương tiện",
    25: "Khách quan, trung thực", 26: "Schema Article + FAQPage", 27: "Schema FAQ khớp nguyên văn",
    28: "Speakable (TL;DR đọc to)", 29: "Liên kết nguồn sống", 30: "Tác giả định danh (Person)",
    31: "Liên kết thực thể nội bộ", 32: "AIO score ≥ 70", 33: "Key Takeaways", 34: "Chú thích ảnh",
    35: "Tóm tắt tiếng Anh 200 từ", 36: "Sensor Sony số 1 thế giới", 37: "Hệ sinh thái ngàm E",
    38: "Triết lý KANDO & cân bằng", 39: "Không kết luận đối thủ tốt hơn", 40: "Kết bài KANDO",
}
GROUPS = [("SEO", 1, 10), ("AIO", 11, 25), ("Schema", 26, 35), ("Brand", 36, 40)]
REQUIRED = {1, 11, 14, 15, 17}
# Tiêu chí không có máy chấm: người duyệt. Ghi chú là việc cần kiểm.
MANUAL = {
    20: "Đối chiếu câu hỏi với paa_generator",
    24: "Nếu có video: mô tả hoặc tóm tắt nội dung",
    25: "Nêu điểm mạnh và điểm cần cân nhắc, không quảng cáo thô",
    28: "TL;DR đọc to trong 20–30 giây",
    30: "Author Person có sameAs và knowsAbout",
    31: "Nối tới các bài cùng hệ sinh thái ngàm E",
    34: "Chú thích ảnh có thông số máy, ống kính, bối cảnh",
    35: "Tóm tắt tiếng Anh 200 từ (tùy chọn)",
}
# Mục legacy của seo_audit -> số tiêu chí checklist (chỉ dùng khi không có nguồn chuyên biệt).
# 5 (link) có nguồn riêng là links(); 16 (số liệu) và 25 (khách quan) có nguồn aio; 32 không chấm (tính từ AIO).
SEO_MAP = {1: [1], 2: [2], 3: [2], 4: [8], 5: [4], 6: [11], 7: [3], 8: [15], 9: [7], 11: [14], 12: [13],
           14: [19], 15: [17], 18: [9, 10], 19: [26], 20: [6], 22: [21], 24: [3], 26: [27]}
ORDER = {"aio": 0, "brand": 1, "links": 2, "citation": 2, "seo": 4}
SEO_STATUS = {"Đạt": "pass", "Chưa đạt": "fail", "Một phần": "fail", "Cần người duyệt": "manual", "N/A": "na"}


def _from_finding(f: dict, source: str) -> dict:
    st = "manual" if f.get("manual") else ("pass" if f["pass"] else "fail")
    return {"source": source, "status": st, "evidence": f["evidence"],
            "fix": f["fix"], "line": f["line"], "quote": f["quote"]}


def _from_seo(it: dict) -> dict:
    return {"source": "seo", "status": SEO_STATUS.get(it["status"], "manual"), "evidence": it["evidence"],
            "fix": it["fix"], "line": it["line"], "quote": it["quote"]}


def _from_links(a) -> dict:
    """Tiêu chí 5: 2–5 link nội bộ, 1–3 link ngoài. Placeholder [link nội bộ: …] tính là nội bộ."""
    ls = links(a)
    inner = [x for x in ls if x["internal"]]
    outer = [x for x in ls if not x["internal"]]
    ni, ne = len(inner), len(outer)
    fixes, over = [], []
    if ni < 2:
        fixes.append(f"Thêm {2 - ni} link nội bộ tới bài cùng hệ sinh thái trong thân bài")
    if ni > 5:
        fixes.append("Giữ 2–5 link nội bộ, gỡ bớt link thừa")
        over += inner
    if ne < 1:
        fixes.append("Thêm 1 link nguồn ngoài (Sony official hoặc DPReview) trong thân bài")
    if ne > 3:
        fixes.append("Giữ 1–3 link nguồn ngoài, gỡ bớt link thừa")
        over += outer
    hits = [(ln, quote(a.lines[ln - 1])) for ln in sorted({x["line"] for x in over})]
    return finding(5, "Liên kết trong & ngoài", not fixes, f"internal {ni} (cần 2–5), external {ne} (cần 1–3)",
                   "; ".join(fixes), hits)


def _from_citation(c: dict) -> dict:
    dead = next((d for d in c["details"] if d["alive"] is False), {"line": 0, "url": ""})
    if c["total_links"] == 0:
        st, ev, fix = "fail", "Không có link nguồn nào", "Thêm 1 link Sony official và 1 link DPReview"
    elif c["dead"]:
        st, ev, fix = "fail", f"{c['dead']} link chết", "Thay hoặc gỡ link chết"
    elif c["tier1_count"] == 0:
        st, ev, fix = "fail", "Thiếu nguồn Sony official (Tier 1)", "Thêm link sony.com.vn hoặc sony.com"
    elif c["alive"] == 0:
        st, ev, fix = "not_checked", f"Có {c['tier1_count']} nguồn Tier 1, chưa kiểm được link sống", \
            "Chạy lại với check_links=True"
    else:
        st, ev, fix = "pass", f"{c['tier1_count']} nguồn Tier 1, {c['alive']} link sống", ""
    return {"source": "citation", "status": st, "evidence": ev, "fix": fix, "line": dead["line"],
            "quote": quote(dead["url"]) if dead["url"] else ""}


def _decide(entries: list[dict]) -> dict:
    """Máy thắng người duyệt. Trong nguồn máy ưu tiên nhất, fail thắng pass."""
    machine = [e for e in entries if e["status"] in ("pass", "fail")]
    if machine:
        top = min(ORDER[e["source"]] for e in machine)
        same = [e for e in machine if ORDER[e["source"]] == top]
        return next((e for e in same if e["status"] == "fail"), same[0])
    for st in ("not_checked", "manual", "na"):
        hit = next((e for e in entries if e["status"] == st), None)
        if hit:
            return hit
    return {"source": "none", "status": "manual", "evidence": "", "fix": "", "line": 0, "quote": ""}


def blog_audit(markdown: str, primary_keyword: str = "", secondary_keywords: Optional[list[str]] = None,
               check_links: bool = False, today: str = "") -> dict:
    """
    Tool MCP: blog_audit (chỉ đọc)
    Input: markdown; primary_keyword (trống thì lấy từ frontmatter); secondary_keywords;
           check_links (True: HEAD từng link, chậm); today (YYYY-MM-DD, '' = hôm nay)
    Output: overall_score, verdict (Đạt ≥80 / Cần sửa 60–79 / Thấp <60; có tiêu chí bắt buộc fail thì không Đạt),
            verdict_reason, groups, failed (chỉ fail), manual_review, not_applicable, not_checked,
            aio_group_score, placeholders, raw
    """
    from . import seo_audit  # lazy: __init__ import module này trước khi seo_audit được định nghĩa

    a = as_article(markdown)
    d = as_date(today)
    kw = (primary_keyword or a.fm.get("primary_keyword") or "").strip()

    aio = aio_audit(a, kw, today=d.isoformat())
    brand = brand_voice_checker(a)
    seo = seo_audit(a, kw, secondary_keywords)
    cite = citation_checker(a.raw, check_links=check_links)
    fresh = freshness_check(a, today=d.isoformat())

    cands = {cl: [] for cl in NAMES}
    for f in aio["items"]:
        cands[f["criterion"]].append(_from_finding(f, "aio"))
    for f in brand["items"]:
        cands[f["criterion"]].append(_from_finding(f, "brand"))
    for it in seo["items"]:
        for cl in SEO_MAP.get(it["id"], []):
            cands[cl].append(_from_seo(it))
    cands[5].append(_from_finding(_from_links(a), "links"))
    cands[29].append(_from_citation(cite))
    cands[32].append({"source": "derived", "status": "na", "evidence": "derived", "fix": "", "line": 0, "quote": ""})
    for cl, note in MANUAL.items():
        cands[cl].append({"source": "manual", "status": "manual", "evidence": "Cần người duyệt", "fix": note,
                          "line": 0, "quote": ""})

    final = {cl: _decide(cands[cl]) for cl in NAMES}
    groups = {g: {"passed": 0, "checked": 0, "manual": 0, "not_checked": 0} for g, _, _ in GROUPS}
    failed, manual_review, not_checked, not_applicable = [], [], [], []
    checked = passed = 0
    for cl, r in final.items():
        g = next(name for name, lo, hi in GROUPS if lo <= cl <= hi)
        st = r["status"]
        row = {"id": cl, "group": g, "item": NAMES[cl]}
        if st in ("pass", "fail"):
            checked += 1
            groups[g]["checked"] += 1
            if st == "pass":
                passed += 1
                groups[g]["passed"] += 1
                continue
            failed.append({**row, "required": cl in REQUIRED, "evidence": r["evidence"],
                           "line": r["line"], "quote": r["quote"], "fix": r["fix"]})
        elif st == "manual":
            groups[g]["manual"] += 1
            manual_review.append({**row, "evidence": r["evidence"], "line": r["line"], "quote": r["quote"],
                                  "fix": r["fix"]})
        elif st == "not_checked":
            groups[g]["not_checked"] += 1
            not_checked.append({**row, "evidence": r["evidence"], "fix": r["fix"]})
        else:
            not_applicable.append({**row, "reason": r["evidence"]})
    for g in groups:
        c = groups[g]["checked"]
        groups[g]["score"] = round(groups[g]["passed"] * 100 / c) if c else 0

    overall = round(passed * 100 / checked) if checked else 0
    verdict = band(overall)
    required_failed = [cl for cl in sorted(REQUIRED) if final[cl]["status"] == "fail"]
    verdict_reason = ""
    if required_failed:
        verdict_reason = "Chưa đạt tiêu chí bắt buộc: " + ", ".join(f"{cl} {NAMES[cl]}" for cl in required_failed)
        if verdict == "Đạt":
            verdict = "Cần sửa"
    aio_group = groups["AIO"]["score"]
    body = fold(a.prose)
    ph = next((f for f in aio["items"] if f["criterion"] == 17), None)

    return {
        "keyword": kw,
        "today": d.isoformat(),
        "overall_score": overall,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "passed": f"{passed}/{checked}",
        "aio_group_score": aio_group,
        "aio_group_verdict": band(aio_group),
        "groups": groups,
        "failed": failed,
        "manual_review": manual_review,
        "not_checked": not_checked,
        "not_applicable": not_applicable,
        "placeholders": ph["hits"] if ph else [],
        "required_failed": required_failed,
        "complete": not required_failed,
        "secondary_keywords": {k: body.count(fold(k)) for k in (secondary_keywords or []) if k.strip()},
        "raw": {"aio": aio, "seo": seo, "brand": brand, "citation": cite, "freshness": fresh},
    }
