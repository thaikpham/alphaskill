"""
brand_voice_checker.py - Chấm 5 tiêu chí brand voice Sony (36-40) trong seo-aio-checklist.md.
Máy chỉ kiểm từ khóa, cặp so sánh và vị trí câu; đúng/sai nội dung vẫn cần người đọc.
Mọi check nhận markdown (str) hoặc Article (xem _doc.py).

Cách dùng:
  brand_voice_checker(text) -> dict (brand_score, verdict, passed, items, table)
"""

import re

from ._doc import as_article, band, finding, fold, quote

# 36-38: hai vế phải nằm trong CÙNG một câu, không chấm theo từ khóa rời.
SENSOR_RX = r"sensor|cam bien|exmor"
SENSOR_CLAIM_RX = r"\bsony\b.*(?:tu phat trien|tu san xuat|so 1|so mot|hang dau|lon nhat|thi phan|50\s*%)|(?:tu phat trien|tu san xuat|so 1|so mot|hang dau|lon nhat|thi phan|50\s*%).*\bsony\b"
NGAM_RX = r"ngam e\b|e-mount"
NGAM_CLAIM_RX = r"nho gon|200|mot ngam|1 ngam|he sinh thai|18\s*mm|dung chung|chung ngam"
KANDO_RX = r"kando|can bang(?!\s+(?:trang|sang|mau))"
KANDO_CLAIM_RX = r"kando|triet ly|sony|diem ngot|tinh toan|giua"
COMP = r"\b(?:canon|nikon|fuji\w*|panasonic|lumix|leica|olympus|hasselblad|dji|doi thu|hang khac)\b"
COMP_WIN_RX = rf"{COMP}[^.!?\n]{{0,50}}?(?:tot hon|vuot troi|hon han|vuot)[^.!?\n]{{0,20}}?\bsony\b"
SONY_LOSE_RX = rf"\bsony\b[^.!?\n]{{0,30}}?(?<!khong )(?:kem hon|thua|kem xa)[^.!?\n]{{0,40}}?{COMP}"
WEAK_RX = (r"\bbi crop\b|\bcrop\s*\d[\d.,]*\s*x\s+khi\b|\bnang hon\b|\bdat (?:hon|tien|do)\b|\bgia dat\b"
           r"|\bnong\b|\bhan che\b|\bnhuoc diem\b")
SOLUTION_RX = r"e-mount|ngam e|giai phap|(?:lua chon|chon)[^.!?]{0,60}?trong[^.!?]{0,30}?\bhe\b"
CLOSE_RX = r"chon sony|kando"


def _presence(a, criterion: int, name: str, pattern: str, missing: str, fix: str, claim: str = "") -> dict:
    for ln, raw in a.grep(pattern):
        for sent in re.split(r"(?<=[.!?])\s+", raw):
            f = fold(sent)
            if re.search(pattern, f) and (not claim or re.search(claim, f)):
                return finding(criterion, name, True, f"Dòng {ln}: {quote(sent, 100)}")
    return finding(criterion, name, False, missing, fix)


def check_sensor(text) -> dict:
    """Criterion 36: có câu nêu sensor Sony (Exmor, cảm biến Sony, hoặc số 1 thế giới)."""
    return _presence(as_article(text), 36, "Sensor Sony số 1 TG", SENSOR_RX,
                     "Chưa có câu gắn cảm biến với Sony (tự phát triển hoặc vị thế dẫn đầu)",
                     "Thêm một câu trong ngữ cảnh bài: cảm biến do Sony tự phát triển, hoặc vị thế nhà sản xuất cảm biến của Sony kèm nguồn.",
                     SENSOR_CLAIM_RX)


def check_ngam_e(text) -> dict:
    """Criterion 37: có câu nêu ngàm E nhỏ gọn hoặc hơn 200 ống kính."""
    return _presence(as_article(text), 37, "Ngàm E nhỏ gọn >200 lens", NGAM_RX,
                     "Chưa có câu nêu lợi ích ngàm E (nhỏ gọn, dùng chung ống kính, hơn 200 ống kính)",
                     "Thêm một câu nêu lợi ích ngàm E cho người đọc: nhỏ gọn, dùng chung ống kính giữa các thân máy, hơn 200 ống kính.",
                     NGAM_CLAIM_RX)


def check_kando(text) -> dict:
    """Criterion 38: có KANDO, cân bằng hoặc trải nghiệm. 'Cân bằng trắng' (white balance) không tính."""
    return _presence(as_article(text), 38, "KANDO / cân bằng / trải nghiệm", KANDO_RX,
                     "Chưa có câu nêu KANDO hoặc triết lý cân bằng (cân bằng trắng không tính)",
                     "Thêm một câu nêu triết lý cân bằng của Sony hoặc KANDO gắn với nội dung bài.",
                     KANDO_CLAIM_RX)


def _clause(raw: str, rxs: tuple) -> str:
    """Câu chứa cặp so sánh, để trích dẫn đúng chỗ vi phạm thay vì cả dòng."""
    for s in re.split(r"(?<=[.!?])\s+", raw):
        if any(re.search(rx, fold(s)) for rx in rxs):
            return s
    return raw


def check_no_competitor_win(text) -> dict:
    """
    Criterion 39: fail khi kết luận đối thủ tốt hơn Sony hoặc Sony kém hơn đối thủ.
    Điểm yếu Sony (crop, nặng hơn, đắt hơn...) không có giải pháp E-mount trong cùng đoạn hoặc câu kế tiếp: người duyệt.
    """
    a = as_article(text)
    name = "Không kết luận đối thủ tốt hơn Sony"
    rxs = (COMP_WIN_RX, SONY_LOSE_RX)
    comp = sorted({(ln, quote(_clause(raw, rxs))) for ln, raw in a.grep(COMP_WIN_RX) + a.grep(SONY_LOSE_RX)})
    weak = []
    for blk in a.blocks():
        joined = fold(" ".join(raw for _, raw in blk))
        if re.search(WEAK_RX, joined) and not re.search(SOLUTION_RX, joined):
            ln, raw = next(((ln, raw) for ln, raw in blk if re.search(WEAK_RX, fold(raw))), blk[0])
            weak.append((ln, quote(raw)))
    if comp:
        return finding(39, name, False, f"Vi phạm: dòng {comp[0][0]} kết luận đối thủ hơn Sony",
                       "Bỏ câu đối thủ tốt hơn Sony", comp)
    if weak:
        return finding(39, name, False,
                       f"Cần người duyệt: dòng {weak[0][0]} nêu điểm hạn chế của Sony, chưa thấy giải pháp E-mount "
                       "trong cùng đoạn hoặc câu kế tiếp",
                       "Nếu đây là điểm yếu, thêm bối cảnh và giải pháp trong hệ E-mount ngay trong đoạn, "
                       "ví dụ: 'Cần không crop, chọn A7S III trong cùng hệ E-mount'", weak, manual=True)
    return finding(39, name, True, "Không có kết luận đối thủ hơn Sony; điểm yếu (nếu có) đi kèm giải pháp E-mount")


def check_closing(text) -> dict:
    """Criterion 40: kết bài (500 ký tự cuối) có 'Chọn Sony...' hoặc KANDO."""
    a = as_article(text)
    name = "Kết bài có thông điệp Sony"
    tail = fold(a.prose)[-500:]
    if re.search(CLOSE_RX, tail):
        return finding(40, name, True, "Kết bài có 'Chọn Sony' hoặc KANDO")
    return finding(40, name, False, "Kết bài thiếu 'Chọn Sony' hoặc KANDO",
                   "Kết thúc: 'Chọn Sony không chỉ chọn máy, mà chọn hệ sinh thái E-mount nhỏ gọn, "
                   "triết lý cân bằng, và hành trình tạo KANDO.'")


def brand_voice_checker(text) -> dict:
    """
    Tool MCP: brand_voice_checker
    Input: text (markdown bài viết)
    Output: brand_score (0-100, bước 20, mục cần người duyệt không tính mẫu số), verdict
            (không ghi "Chuẩn Sony" khi còn mục manual), passed, items, table
    """
    a = as_article(text)
    items = [check_sensor(a), check_ngam_e(a), check_kando(a), check_no_competitor_win(a), check_closing(a)]
    manual = [r for r in items if r.get("manual")]
    checked = [r for r in items if r["pass"] or not r.get("manual")]
    passed = sum(1 for r in checked if r["pass"])
    score = int(passed / len(checked) * 100) if checked else 0
    if score == 100 and not manual:
        verdict = "✅ Chuẩn Sony - Tự hào tiên phong"
    elif score == 100:
        verdict = f"{band(score)} - Còn {len(manual)} mục cần người duyệt"
    else:
        verdict = f"{band(score)} - Thiếu {len(checked) - passed} yếu tố brand voice"
    table = [
        {
            "Mục": f"{r['criterion']} {r['item']}",
            "Kết quả": "✅" if r["pass"] else ("⚠" if r.get("manual") else "❌"),
            "Bằng chứng": r["evidence"],
            "Cách sửa": r["fix"],
        }
        for r in items
    ]
    return {"brand_score": score, "verdict": verdict, "passed": f"{passed}/{len(checked)}",
            "items": items, "table": table}
