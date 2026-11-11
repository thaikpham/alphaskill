"""
freshness_check.py - Kiểm tra độ mới: mốc 'Cập nhật MM/YYYY' hoặc ngày (kể cả frontmatter updated).
Mới = mốc gần nhất trong vòng 365 ngày tính tới today. Mọi check nhận markdown (str) hoặc Article.

Cách dùng:
  freshness_check(text, today="") -> dict (freshness_score, verdict, has_current_update, issues, ...)
"""

import re

from ._doc import as_article, as_date, fold, stamps


def freshness_check(text, today="") -> dict:
    """Tool MCP: freshness_check. today: YYYY-MM-DD hoặc '' (hôm nay)."""
    a = as_article(text)
    d = as_date(today)
    st = sorted(stamps(a), key=lambda s: s["date"], reverse=True)
    fix = f"Thêm dòng 'Cập nhật {d:%m/%Y}: [nội dung cập nhật]'"

    issues, suggestions = [], []
    latest = st[0]["date"] if st else None
    has_current = latest is not None and (d - latest).days <= 365
    if latest is None:
        freshness_score = 30
        issues.append("Không tìm thấy mốc cập nhật")
        suggestions.append(fix)
    elif not has_current:
        freshness_score = 50
        issues.append(f"Mốc cập nhật mới nhất {latest:%m/%Y} đã quá 365 ngày")
        suggestions.append(fix)
    else:
        freshness_score = 90

    prose = a.prose
    years = sorted({int(y) for y in re.findall(r"20\d\d", prose)})
    old_years = [y for y in years if y < d.year - 1]
    if old_years and str(d.year) not in prose:
        issues.append(f"Bài có năm cũ: {old_years[:2]}")

    if "zv-e10" in fold(prose) and "zv-e10 ii" not in fold(prose) and d.year >= 2025:
        issues.append("Lỗi thời: ZV-E10 (đã có ZV-E10 II ra 2024)")

    if freshness_score >= 80:
        verdict = f"Tươi mới - Có mốc cập nhật {latest:%m/%Y}"
    elif freshness_score >= 50:
        verdict = f"Hơi cũ - Cần thêm dòng Cập nhật {d:%m/%Y}"
    else:
        verdict = "Cũ - Thiếu mốc cập nhật, AIO sẽ ưu tiên bài mới hơn"

    auto_updates = [
        f"Cập nhật {d:%m/%Y}: Xác minh giá và thông số trên sony.com.vn",
        f"Cập nhật {d:%m/%Y}: Kiểm tra firmware mới nhất tại Sony official",
        f"Cập nhật {d:%m/%Y}: So sánh với máy mới ra gần đây",
    ]

    return {
        "freshness_score": freshness_score,
        "verdict": verdict,
        "dates_found": [s["date"].isoformat() for s in st[:5]],
        "latest": f"{latest:%m/%Y}" if latest else "",
        "has_current_update": has_current,
        "issues": issues,
        "suggestions": suggestions,
        "auto_update_snippets": auto_updates[:3],
        "today": d.isoformat(),
    }
