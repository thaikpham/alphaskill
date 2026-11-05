
import re
import datetime

def freshness_check(text: str, today=None):
    """Check if blog post is fresh. today: optional datetime.date for testing."""
    if today is None:
        today = datetime.date.today()

    current_month_year = today.strftime("%m/%Y")
    current_year = today.year

    issues = []
    suggestions = []

    dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|Cap nhat.*\d{4}|202[3-5]', text)
    has_update_current = bool(re.search(rf'Cap nhat.*{current_year}|{current_month_year}|{current_year}', text))

    if not dates:
        issues.append("Khong tim thay ngay xuat ban/cap nhat")
        suggestions.append(f"Them dong: Cap nhat {current_month_year}: ...")
        freshness_score = 30
    elif not has_update_current:
        issues.append(f"Bai co ngay cu: {dates[:2]} - chua cap nhat {current_year}")
        suggestions.append(f"Them: Cap nhat {current_month_year}: Gia va thong so hien tai...")
        freshness_score = 50
    else:
        freshness_score = 90

    # Check for stale year references (more than 1 year old)
    old_years = sorted({y for y in re.findall(r'20\d\d', text) if int(y) < current_year - 1})
    if old_years and str(current_year) not in text:
        issues.append(f"Bai co nam cu: {old_years[:2]}")

    # Flag outdated terms
    outdated_terms = []
    if "ZV-E10" in text and "ZV-E10 II" not in text and current_year >= 2025:
        outdated_terms.append("ZV-E10 (da co ZV-E10 II ra 2024)")

    for term in outdated_terms:
        issues.append(f"Loi thoi: {term}")

    auto_updates = [
        f"Cap nhat {current_month_year}: Xac minh gia va thong so tren sony.com.vn",
        f"Cap nhat {current_month_year}: Kiem tra firmware moi nhat tai Sony official",
        f"Cap nhat {current_month_year}: So sanh voi may moi ra gan day",
    ]

    if freshness_score >= 80:
        verdict = f"Tuoi moi - Co cap nhat {current_year}"
    elif freshness_score >= 50:
        verdict = f"Hoi cu - Can them dong Cap nhat {current_month_year}"
    else:
        verdict = "Cu - Thieu ngay, AIO se uu tien bai moi hon"

    return {
        "freshness_score": freshness_score,
        "verdict": verdict,
        "dates_found": dates[:5],
        "has_current_update": has_update_current,
        "issues": issues,
        "suggestions": suggestions,
        "auto_update_snippets": auto_updates[:3]
    }
