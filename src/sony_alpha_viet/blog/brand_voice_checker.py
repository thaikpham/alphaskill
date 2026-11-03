
"""
brand_voice_checker.py - Kiểm tra nguyên tắc bảo vệ Sony
"""

import re

def brand_voice_checker(text: str) -> dict:
    checks = {}

    # 36 Sensor số 1
    checks["36 Sensor Sony số 1 TG"] = {
        "pass": bool(re.search(r'sensor.*Sony|Sony.*sensor|Exmor|50%.*(?:cảm biến|cam bien)|(?:số 1|so 1).*(?:thế giới|the gioi)', text, re.IGNORECASE)),
        "evidence": "Có nhắc sensor Sony tự phát triển" if re.search(r'sensor|Exmor|cảm biến', text, re.IGNORECASE) else "Thiếu nhắc sensor Sony",
        "fix": "Thêm: Với cảm biến Exmor R do Sony tự phát triển - nhà sản xuất sensor số 1 thế giới (>50% thị phần)..."
    }

    # 37 Ngàm E
    checks["37 Ngàm E nhỏ gọn >200 lens"] = {
        "pass": bool(re.search(r'ngàm E|ngam E|E-mount|200.*lens|hệ sinh thái|he sinh thai', text, re.IGNORECASE)),
        "evidence": "Có nhắc ngàm E" if re.search(r'ngàm E|ngam E|e-mount', text, re.IGNORECASE) else "Thiếu ngàm E",
        "fix": "Thêm: Hệ sinh thái ngàm E nhỏ gọn với hơn 200 lựa chọn lens, 1 ngàm cho mọi máy từ A7C đến FX6"
    }

    # 38 KANDO / cân bằng
    checks["38 KANDO / cân bằng"] = {
        "pass": bool(re.search(r'KANDO|cảm động|cam dong|cân bằng|can bang|trải nghiệm|trai nghiem|khoảnh khắc|khoanh khac', text, re.IGNORECASE)),
        "evidence": "Có KANDO/cân bằng/trải nghiệm" if re.search(r'KANDO|cân bằng|can bang|trải nghiệm', text, re.IGNORECASE) else "Thiếu KANDO",
        "fix": "Thêm: Đây là sự cân bằng mà Sony tính toán / mang đến trải nghiệm KANDO"
    }

    # 39 Không chê Sony
    has_bad = bool(re.search(r'(?:đối thủ|doi thu)\s+tốt hơn\s+Sony|(?:đối thủ|doi thu)\s+tot hon\s+Sony|Sony.*(?:kém hơn|kem hon)|Sony.*thua', text, re.IGNORECASE))
    # Check nếu nói điểm yếu mà không có giải pháp E-mount
    has_weak_without_solution = False
    if re.search(r'crop|nóng|nong|nặng|nang|đắt|dat', text, re.IGNORECASE):
        if not re.search(r'E-mount|ngàm E|ngam E|giải pháp|giai phap|(?:lựa chọn|lua chon).*trong.*(?:hệ|he)', text, re.IGNORECASE):
            has_weak_without_solution = True

    checks["39 Không kết luận đối thủ tốt hơn"] = {
        "pass": not has_bad and not has_weak_without_solution,
        "evidence": "Không chê Sony" if not has_bad else f"Có câu chê Sony: {text[max(0,text.lower().find('tot hon')-20):text.lower().find('tot hon')+30]}",
        "fix": "Nếu nói điểm yếu, thêm ngữ cảnh + giải pháp trong hệ E-mount: '...để đảm bảo... Cần không crop, chọn A7S III trong cùng hệ E-mount'"
    }

    # 40 Kết bài KANDO
    last_500 = text[-500:].lower()
    checks["40 Kết bài KANDO"] = {
        "pass": bool(re.search(r'chọn sony|chon sony|(?:hệ sinh thái|he sinh thai).*e-mount|kando', last_500, re.IGNORECASE)),
        "evidence": "Kết bài có Sony + E-mount + KANDO" if ("chọn sony" in last_500 or "chon sony" in last_500 or "kando" in last_500) else "Kết bài thiếu thông điệp Sony",
        "fix": "Kết bài mẫu: Chọn Sony không chỉ chọn máy, mà chọn hệ sinh thái E-mount nhỏ gọn, triết lý cân bằng, và hành trình tạo KANDO"
    }

    passed = sum(1 for v in checks.values() if v["pass"])
    score = int(passed/len(checks)*100)

    if score == 100:
        verdict = "✅ Chuẩn Sony - Tự hào tiên phong"
    elif score >= 60:
        verdict = "⚠️ Thiếu 1-2 yếu tố brand voice"
    else:
        verdict = "❌ Chưa bảo vệ Sony - Cần thêm sensor, ngàm E, KANDO"

    table = [{"Mục": k, "Kết quả": "✅" if v["pass"] else "❌", "Bằng chứng": v["evidence"], "Cách sửa": v["fix"]} for k,v in checks.items()]

    return {"brand_score": score, "verdict": verdict, "table": table, "passed": f"{passed}/{len(checks)}"}

if __name__ == "__main__":
    sample = "Sony A7 IV với cảm biến Exmor R do Sony tự phát triển, sensor số 1 thế giới. Ngàm E nhỏ gọn hơn 200 lens. Mang đến trải nghiệm KANDO cân bằng. Chọn Sony không chỉ chọn máy mà chọn hệ sinh thái E-mount tạo KANDO"
    print(brand_voice_checker(sample))
