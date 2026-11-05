
"""
paa_generator.py - Tool gợi ý 10 câu People Also Ask cho từ khóa Sony Alpha
Không cần internet, dùng template + entity Sony

Cách dùng:
  paa_generator(primary_keyword, audience="thợ cưới", models=["A7 IV", "A7R V"]) -> list câu hỏi

LƯU Ý: Tất cả hints là template. Mọi số liệu cụ thể (MP, shot, firmware, giá...) phải xác minh trước khi công bố.
"""

from typing import List, Dict

TEMPLATES = [
    "{kw} có tốt cho {audience} không?",
    "{kw} khác gì {other_model}?",
    "{kw} có chống rung IBIS không?",
    "{kw} quay video 4K có crop không?",
    "{kw} pin dùng được bao lâu khi chụp cưới?",
    "{kw} có Eye AF cho mắt động vật không?",
    "{kw} giá bao nhiêu ở Việt Nam 2026?",
    "{kw} nên dùng với lens nào cho {audience}?",
    "{kw} có quá nặng để chụp cả ngày không?",
    "{kw} có 2 khe thẻ nhớ không?",
    "{kw} file RAW nặng bao nhiêu MB?",
    "{kw} có S-Log3 để quay cưới không?",
]

def paa_generator(primary_keyword: str, audience: str = "thợ chụp cưới", models: List[str] = None) -> Dict:
    """
    Tool MCP: paa_generator
    Input: primary_keyword (VD: "Sony A7 IV hay A7R V"), audience, models
    Output: 10 câu hỏi PAA + gợi ý trả lời ngắn 40-70 từ
    """
    if not models:
        # Tự tách từ keyword
        if "hay" in primary_keyword:
            parts = primary_keyword.split("hay")
            models = [p.strip() for p in parts[:2]]
        else:
            models = [primary_keyword, "A7 IV"]

    kw = primary_keyword
    other = models[1] if len(models) > 1 else "A7R V"

    questions = []
    for tmpl in TEMPLATES[:10]:
        q = tmpl.format(kw=kw, audience=audience, other_model=other)
        questions.append(q)

    # Gợi ý trả lời mẫu cho 3 câu đầu để AI hiểu format
    # Lưu ý: không ghi số cụ thể, dùng placeholder [thông số từ sony.com.vn]
    suggestions = [
        {
            "question": questions[0],
            "answer_hint": f"Có, {models[0]} tốt cho {audience} vì pin dùng được lâu, có [số khe thẻ từ sony.com.vn] khe thẻ, Eye AF chính xác. Xác minh pin shots, trọng lượng so với các model khác tại sony.com.vn.",
            "word_count": "40-70 từ, tự đứng được"
        },
        {
            "question": questions[1],
            "answer_hint": f"{models[0]} khác {other} ở độ phân giải: {models[0]} có [MP1 từ sony.com.vn] cân bằng, {other} có [MP2 từ sony.com.vn] chi tiết cao nhưng file nặng hơn. Xác minh thông số file size trên sony.com.vn.",
            "word_count": "40-70 từ"
        },
        {
            "question": questions[2],
            "answer_hint": "Có, cả 2 máy đều có chống rung IBIS với [thông số trục và stop từ sony.com.vn]. Xác minh khả năng chụp tốc độ thấp khi có ánh sáng tối.",
            "word_count": "40-70 từ"
        }
    ]

    return {
        "primary_keyword": primary_keyword,
        "audience": audience,
        "models": models,
        "paa_questions": questions,
        "suggestions": suggestions,
        "instruction": "Trả lời mỗi câu 40-70 từ, tự đứng được, có số liệu + nguồn Sony official, ví dụ VN. Dùng để làm FAQ trong bài."
    }

if __name__ == "__main__":
    print(paa_generator("Sony A7 IV hay A7R V", "thợ chụp cưới"))
