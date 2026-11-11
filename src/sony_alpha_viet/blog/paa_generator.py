"""
paa_generator.py - Tool gợi ý 10 câu People Also Ask cho từ khóa Sony Alpha
Không cần internet, dùng template + entity Sony

Cách dùng:
  paa_generator(primary_keyword, audience="người chụp ảnh", models=None) -> list câu hỏi

LƯU Ý: Tất cả hints là template. Mọi số liệu cụ thể (MP, shot, firmware, giá...) phải xác minh trước khi công bố.
"""

import re
from typing import List, Dict

TEMPLATES = [
    "{kw} có tốt cho {audience} không?",
    "{kw} khác gì {other_model}?",
    "{kw} có chống rung IBIS không?",
    "{kw} quay video 4K có crop không?",
    "{kw} pin dùng được bao lâu?",
    "{kw} có Eye AF cho chủ thể chuyển động không?",
    "{kw} giá bao nhiêu ở Việt Nam?",
    "{kw} nên dùng với lens nào?",
    "{kw} có quá nặng để mang cả ngày không?",
    "{kw} có 2 khe thẻ nhớ không?",
    "{kw} file RAW nặng bao nhiêu MB?",
    "{kw} có S-Log3 để quay video không?",
]

def paa_generator(primary_keyword: str, audience: str = "người chụp ảnh", models: List[str] = None) -> Dict:
    """
    Tool MCP: paa_generator
    Input: primary_keyword (VD: "Sony A7 IV hay A7R V"), audience, models
    Output: 10 câu hỏi PAA + gợi ý trả lời ngắn 40-70 từ
    """
    if not models:
        # Tự tách từ keyword theo "hay" đứng riêng (không tách trong "thay", "hayabusa")
        parts = re.split(r"\s+hay\s+", primary_keyword, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2 and all(p.strip() for p in parts):
            models = [p.strip() for p in parts]
        else:
            models = [primary_keyword, "model khác"]

    kw = primary_keyword
    other = models[1] if len(models) > 1 else "model khác"

    questions = []
    for tmpl in TEMPLATES[:10]:
        q = tmpl.format(kw=kw, audience=audience, other_model=other)
        questions.append(q)

    # Gợi ý trả lời mẫu cho 3 câu đầu để AI hiểu format
    # Lưu ý: không ghi số cụ thể, không mở bằng "Có,"; dùng placeholder [..] để người viết điền có nguồn
    suggestions = [
        {
            "question": questions[0],
            "answer_hint": f"[Trả lời thẳng: {models[0]} hợp với {audience} ở điểm nào, nêu tính năng chính từ sony.com.vn]. Xác minh thông số pin, trọng lượng trên sony.com.vn trước khi công bố.",
            "word_count": "40-70 từ, tự đứng được"
        },
        {
            "question": questions[1],
            "answer_hint": f"[Nêu khác biệt chính giữa {models[0]} và {other}, mỗi ý kèm đặc điểm từ sony.com.vn]. Xác minh thông số chi tiết trên sony.com.vn trước khi công bố.",
            "word_count": "40-70 từ"
        },
        {
            "question": questions[2],
            "answer_hint": "[Nêu máy có IBIS hay không, kèm thông số trục và stop từ sony.com.vn]. Xác minh khả năng chụp tốc độ chậm trong ánh sáng yếu trước khi công bố.",
            "word_count": "40-70 từ"
        }
    ]

    return {
        "primary_keyword": primary_keyword,
        "audience": audience,
        "models": models,
        "paa_questions": questions,
        "suggestions": suggestions,
        "instruction": "Trả lời mỗi câu 40-70 từ, tự đứng được, có số liệu + nguồn Sony official, ví dụ thực tế. Dùng để làm FAQ trong bài."
    }

if __name__ == "__main__":
    print(paa_generator("Sony A7 IV hay A7R V", "người chụp ảnh"))
