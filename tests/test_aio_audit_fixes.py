"""
tests/test_aio_audit_fixes.py - Test bug fixes in aio_audit
Chạy: uv run pytest tests/test_aio_audit_fixes.py -q
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, 'src')

from sony_alpha_viet.blog.aio_audit import (aio_audit, has_tldr, check_h2_self_contained, check_faq,
                                            check_entity, check_placeholder)
from sony_alpha_viet.blog.paa_generator import paa_generator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "howto-article.md"


def load_fixture() -> str:
    assert FIXTURE.exists(), f"Thiếu fixture: {FIXTURE}"
    return FIXTURE.read_text(encoding="utf-8")


def test_fix1_tldr_bullet_list_word_count():
    """Fix 1: TL;DR with bullet list should count words from all items, not as 1 word."""
    article = """# Test Article

**TL;DR**

- AWB (Auto White Balance) chọn dựa trên trung bình ánh sáng khung; nó sai khi có một màu ánh sáng chiếm ưu thế.
- Ba tình huống: đèn huỳnh quang (xanh lạnh), lửa hay đèn sợi (cam nóng), hoặc vật quá sáng/tối làm nhiễu.
- Ba công cụ sửa: preset (Daylight, Incandescent, bốn mức Fluor.), chọn Kelvin tay, hoặc chỉnh Shift A/B.

## Next Section
Content here.
"""
    result = has_tldr(article)
    assert result["pass"] is True, result["evidence"]
    assert "3 bullet" in result["evidence"]
    print(f"Fix 1 PASS: TL;DR word count = {result['evidence']}")


def test_fix2_faq_section_regex_not_truncate_at_h3():
    """Fix 2: FAQ section regex should not stop at ### headings (stop at ## or # only)."""
    article = """# Main Title

Content before FAQ.

## Câu hỏi thường gặp

### Question 1?
Answer to question 1 contains at least 40 words explaining the full concept and providing detailed information about how the system works. This is necessary information for readers understanding the topic. Important details here are also included with additional context and explanation.

### Question 2?
Answer to question 2 with more than 40 words explaining concepts thoroughly and providing specific details. This is a proper detailed answer with comprehensive information. Very important information included here for complete understanding of topic and its applications in real world scenarios.

### Question 3?
Answer to question 3 with 40-70 words providing properly formatted explanation. Additional details and context provided here for clarity and understanding. More information to reach the word count requirement is provided and necessary for complete comprehension of topic being discussed here.

## Next Section
More content after FAQ.
"""
    result = check_faq(article)
    assert result["pass"] is True, result["evidence"]
    assert "FAQ 3 câu" in result["evidence"]
    print(f"Fix 2 PASS: FAQ finds 3 questions: {result['evidence']}")


def test_fix3_h2_sentence_split_on_period_space_not_all_dots():
    """Fix 3: H2 first sentence should split on '. ' or '? ' not on all '.' (handles f/5.6, 24.2 MP, etc.)."""
    article = """# Test

## First Heading with f/5.6 spec

Aperture f/5.6 is common in photography today for capturing images. The first sentence ends here, and this is the second sentence with lots of words explaining the concept thoroughly.

Content continues.
"""
    result = check_h2_self_contained(article)
    assert result["pass"] is True, result["evidence"]
    print(f"Fix 3 PASS: H2 sentence split correctly: {result['evidence']}")


def test_fix4_freshness_evidence_text_conditional():
    """Fix 4: Freshness evidence text should be conditional on actual detection."""
    article = "# Old Article from 2024\n\nNo current date mentioned."
    result = aio_audit(article, "test", "review", today="2026-11-11")
    criterion_23 = [item for item in result["table"] if "Cập nhật" in item["Mục"]][0]
    assert criterion_23["Kết quả"] == "❌ Chưa"
    assert "Không có" in criterion_23["Bằng chứng"]
    print(f"Fix 4 PASS: Freshness evidence conditional: {criterion_23['Bằng chứng']}")


def test_fix5_article_type_howto_skips_vn_example():
    """Fix 5: article_type='howto' should skip criterion 19 VN example requirement."""
    article = """# How To Choose White Balance

**TL;DR**
- Chọn AWB khi ánh sáng trung tính, từ đó bạn có thể sử dụng máy trong nhiều tình huống khác nhau.
- Chọn preset khi biết loại ánh sáng, giúp bạn nhanh chóng điều chỉnh màu sắc theo nhu cầu thực tế.

## Bước 1
Content explaining concepts and providing detailed steps for the process of choosing and implementing white balance settings.

## Bước 2
More content explaining additional steps and procedures for proper white balance adjustment and camera configuration.

## Câu hỏi thường gặp

### Question?
Answer with more than 40 words about the concept explaining thoroughly all aspects. More details here explaining the full process and context needed for proper understanding of techniques and methods.
"""
    result = aio_audit(article, "cách chọn White Balance", "howto")
    criterion_19 = [item for item in result["table"] if "Ví dụ thực tế" in item["Mục"]][0]
    assert criterion_19["Kết quả"] == "✅ Đạt"
    print(f"Fix 5 PASS: article_type=howto skips VN example: {criterion_19['Bằng chứng']}")


def test_fix6_entity_accepts_sony_model_codes():
    """Fix 6: Entity check should accept Sony model codes (ZV-E10, A6400, A7 IV, etc) not just 'sony' + specs."""
    article = """# About ZV-E10

This article discusses the ZV-E10 camera and A6400.

Content about the camera.
"""
    result = check_entity(article, "ZV-E10")
    assert result["pass"] is True
    assert "zv-e10" in result["evidence"].lower()
    print(f"Fix 6 PASS: Entity accepts model codes: {result['evidence']}")


def test_fix7_paa_generator_neutral_defaults():
    """Fix 7: paa_generator should use neutral defaults, not hardcoded models/audience."""
    result = paa_generator("Sony A7 IV")
    hints = " ".join(s.get("answer_hint", "") for s in result["suggestions"])
    assert "[" in hints and "]" in hints
    assert "thợ cưới" not in hints.lower() and "wedding" not in hints.lower()
    assert "A7R V" not in hints
    print("Fix 7 PASS: paa_generator uses neutral defaults")


def test_fixture_howto_article_tldr_word_count():
    """Test howto fixture: TL;DR word count is the real count and inside 40-70."""
    result = has_tldr(load_fixture())
    assert result["pass"] is True, result["evidence"]
    match = re.search(r"TL;DR (\d+) từ", result["evidence"])
    assert match, result["evidence"]
    word_count = int(match.group(1))
    assert 40 <= word_count <= 70, f"TL;DR word count should be 40-70, got {word_count}"
    print(f"Fix: fixture howto TL;DR word count correct: {result['evidence']}")


def test_fixture_howto_article_faq_question_count():
    """Test howto fixture: FAQ question count equals real number of ### questions."""
    fixture = load_fixture()
    result = check_faq(fixture)
    real_questions = len(re.findall(r"^###\s+.*\?", fixture, re.MULTILINE))
    assert real_questions >= 3, f"Fixture should have at least 3 ### questions, got {real_questions}"
    assert result["pass"] is True, result["evidence"]
    assert f"FAQ {real_questions} câu" in result["evidence"]
    print(f"Fix: fixture howto FAQ has {real_questions} questions: {result['evidence']}")


def test_fixture_howto_article_no_hardcoded_values_in_fixes():
    """Test: fix text does not hardcode a persona, a price or a specific model."""
    result = aio_audit(load_fixture(), "AWB", "howto", today="2026-11-11")
    fix_texts = " ".join(item.get("Cách sửa", "") for item in result["table"])
    assert "thợ cưới" not in fix_texts.lower()
    assert "A7 IV" not in fix_texts
    assert not re.search(r"\d+\s?(?:triệu|tr)\b", fix_texts.lower())
    print("Fix: No hardcoded values in fix text")


def test_h2_check_skips_faq_heading():
    text = (
        "## Cách chỉnh ISO Auto trên máy Sony\n\nVào menu Phơi sáng và đặt giới hạn trên cho ISO Auto để ảnh không nhiễu.\n\n"
        "## Câu hỏi thường gặp\n\n### ISO Auto là gì?\n\nMáy tự chọn ISO.\n"
    )
    assert check_h2_self_contained(text)["pass"]


def test_style_lint_allows_vietnamese_reduplicatives():
    from sony_alpha_viet.blog import style_lint
    types = [i["type"] for i in style_lint("Lia máy từ từ theo xe. Hai thanh chạy song parallel. Ảnh đẹp rất rất nhiều.")["issues"]]
    assert types.count("doubled") == 1


def test_regression_placeholder_uppercase_vietnamese():
    """Regression: Uppercase Vietnamese placeholder [CẦN XÁC MINH] should be detected."""
    # Test uppercase variant
    text_upper = "This is important [CẦN XÁC MINH] information."
    result = check_placeholder(text_upper)
    assert result["pass"] is False, "Uppercase [CẦN XÁC MINH] should be detected"
    assert "placeholder" in result["evidence"].lower()

    # Test mixed case variants
    text_mixed = "Verify [cẦN XÁC MINH] this data"
    result = check_placeholder(text_mixed)
    assert result["pass"] is False, "Mixed case placeholder should be detected"


def test_regression_vn_location_lowercase():
    """Regression: Lowercase Vietnamese locations should be detected in criterion 19."""
    # Test lowercase "hà nội"
    text_lowercase = "Cảnh đẹp ở hà nội rất nổi tiếng trong các bộ phim. Chụp ảnh tại đây giúp bạn tạo được những bức ảnh độc đáo với nhiều góc nhìn khác nhau."
    result = aio_audit(text_lowercase, "Sony A7 IV", "review")

    criterion_19 = next((item for item in result["table"] if "Ví dụ thực tế VN" in item["Mục"]), None)
    assert criterion_19 is not None, "Criterion 19 should exist"
    assert criterion_19["Kết quả"] == "✅ Đạt", f"Criterion 19 should pass for lowercase 'hà nội', got: {criterion_19['Bằng chứng']}"

    # Test other lowercase variants
    text_hcm = "Các địa điểm nổi tiếng ở hcm như Nhà thờ Đức Bà rất đẹp khi chụp vào buổi chiều. Ánh sáng vàng làm cho kiến trúc trở nên lộng lẫy và cuốn hút."
    result = aio_audit(text_hcm, "Sony A7 IV", "review")
    criterion_19 = next((item for item in result["table"] if "Ví dụ thực tế VN" in item["Mục"]), None)
    assert criterion_19["Kết quả"] == "✅ Đạt", f"Criterion 19 should pass for lowercase 'hcm', got: {criterion_19['Bằng chứng']}"


if __name__ == "__main__":
    test_fix1_tldr_bullet_list_word_count()
    test_fix2_faq_section_regex_not_truncate_at_h3()
    test_fix3_h2_sentence_split_on_period_space_not_all_dots()
    test_fix4_freshness_evidence_text_conditional()
    test_fix5_article_type_howto_skips_vn_example()
    test_fix6_entity_accepts_sony_model_codes()
    test_fix7_paa_generator_neutral_defaults()
    test_fixture_howto_article_tldr_word_count()
    test_fixture_howto_article_faq_question_count()
    test_fixture_howto_article_no_hardcoded_values_in_fixes()
    print("\nAll fixes PASS")
