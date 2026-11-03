
import re

CURRENT_YEAR = 2026

OLD_PRICE_PATTERNS = [
    (r'A7 IV.*(60|62|65)\s*trieu', "A7 IV gia 60-65tr la gia 2023, nay 2026 con ~52tr body"),
    (r'A7R V.*(85|90|92)\s*trieu', "A7R V gia 90tr la gia 2022, nay ~75tr"),
]

def freshness_check(text: str):
    issues = []
    suggestions = []
    
    dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|Cap nhat.*\d{4}|202[3-5]', text)
    has_update_2026 = bool(re.search(r'Cap nhat.*2026|11/2026|2026', text))
    
    if not dates:
        issues.append("Khong tim thay ngay xuat ban/cap nhat")
        suggestions.append("Them dong: Cap nhat 11/2026: ...")
        freshness_score = 30
    elif not has_update_2026:
        issues.append(f"Bai co ngay cu: {dates[:2]} - chua cap nhat 2026")
        suggestions.append("Them: Cap nhat 11/2026: Gia hien tai...")
        freshness_score = 50
    else:
        freshness_score = 90
    
    for pattern, msg in OLD_PRICE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"Gia cu: {msg}")
            suggestions.append("Sua thanh gia 2026 + ghi '(gia tham khao 11/2026)'")
            freshness_score = min(freshness_score, 60)
    
    outdated_terms = []
    if "ZV-E10" in text and "ZV-E10 II" not in text and CURRENT_YEAR >= 2025:
        outdated_terms.append("ZV-E10 (da co ZV-E10 II ra 2024)")
    
    for term in outdated_terms:
        issues.append(f"Loi thoi: {term}")
    
    auto_updates = [
        "Cap nhat 11/2026: Gia Sony A7 IV body hien ~52tr, A7R V ~75tr tai Sony VN",
        "Cap nhat 11/2026: A7 IV firmware 2.02 them Focus Bracketing",
        "Cap nhat 11/2026: Them so sanh voi A7C II (ra 2023)",
    ]
    
    if freshness_score >= 80:
        verdict = "Tuoi moi - Co cap nhat 2026"
    elif freshness_score >= 50:
        verdict = "Hoi cu - Can them dong Cap nhat 11/2026"
    else:
        verdict = "Cu - Thieu ngay, gia cu, AIO se uu tien bai moi hon"
    
    return {
        "freshness_score": freshness_score,
        "verdict": verdict,
        "dates_found": dates[:5],
        "has_2026_update": has_update_2026,
        "issues": issues,
        "suggestions": suggestions,
        "auto_update_snippets": auto_updates[:3]
    }
