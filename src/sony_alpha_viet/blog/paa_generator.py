
"""
paa_generator.py - Tool gợi ý 10 câu People Also Ask cho từ khóa Sony Alpha
Không cần internet, dùng template + entity Sony

Cách dùng:
  paa_generator(primary_keyword, audience="thợ cưới", models=["A7 IV", "A7R V"]) -> list câu hỏi
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
    suggestions = [
        {
            "question": questions[0],
            "answer_hint": f"Có, {models[0]} rất tốt cho {audience} vì pin 580 shot, 2 khe thẻ, Eye AF mắt người chính xác 94% (nguồn: Sony). Nhược: nặng hơn ZV-E10.",
            "word_count": "45 từ, tự đứng được"
        },
        {
            "question": questions[1],
            "answer_hint": f"{models[0]} khác {other} ở độ phân giải: {models[0]} 33MP cân bằng, {other} 61MP chi tiết cao nhưng file RAW 120MB. Thợ cưới nên chọn {models[0]} để xử lý nhanh.",
            "word_count": "42 từ"
        },
        {
            "question": questions[2],
            "answer_hint": "Có, cả 2 máy đều có IBIS 5 trục 5.5 stop, giúp chụp tốc 1/15s không rung khi chụp tiệc tối không flash.",
            "word_count": "28 từ"
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
