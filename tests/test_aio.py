
"""
tests/test_aio.py - Test cho 4 tool AIO mới v1.2.0
Chạy: uv run pytest tests/test_aio.py -q
Không cần internet
"""

import sys
sys.path.insert(0, 'src')

def test_aio_audit_has_tldr():
    from sony_alpha_viet.blog.aio_audit import aio_audit

    good = """
# Sony A7 IV hay A7R V cho tho cuoi?

TL;DR: A7 IV tot hon cho tho cuoi vi pin lau 580 shot, file nhe 33MP xu ly nhanh, 2 khe the an toan. A7R V tot hon cho phong canh vi 61MP chi tiet cao nhung file RAW 120MB nang may.

## A7 IV la gi?
A7 IV la may full-frame 33MP ra mat 2021, co IBIS 5.5 stop, Eye AF mat nguoi. Tho cuoi o HCM dung 2 nam thay rat ben.

## So sanh chi tiet
Bang so sanh giup AI trich:

| Tieu chi | A7 IV | A7R V |
| Pin | 580 shot | 530 shot |
| Do phan giai | 33MP | 61MP |

## FAQ

A7 IV co chong rung khong? Co, IBIS 5 truc 5.5 stop giup chup toc 1/15s khong rung khi chup tiec toi.

Gia A7 IV bao nhieu 2026? Khoang 52 trieu body, cap nhat 11/2026.

A7 IV co 2 khe the nho khong? Co, 1 khe CFexpress Type A + 1 SD UHS-II.

Cap nhat 11/2026: Gia hien tai 52tr
"""
    res = aio_audit(good, "Sony A7 IV hay A7R V")
    # Sample này phải >=60
    assert res["aio_score"] >= 60, f"Expected >=60, got {res['aio_score']}"
    print(f"test_aio_audit_has_tldr PASS score={res['aio_score']}")

def test_aio_audit_missing_tldr():
    from sony_alpha_viet.blog.aio_audit import aio_audit
    bad = "# Test\n\nNo TLDR, no table, no FAQ"
    res = aio_audit(bad, "A7 IV")
    assert res["aio_score"] < 50
    print("test_aio_audit_missing_tldr PASS")

def test_paa_generator():
    from sony_alpha_viet.blog.paa_generator import paa_generator
    res = paa_generator("Sony A7 IV hay A7R V", "tho chup cuoi")
    assert len(res["paa_questions"]) == 10
    assert "suggestions" in res
    print("test_paa_generator PASS")

def test_citation_checker_with_links():
    from sony_alpha_viet.blog.citation_checker import citation_checker
    text = """
A7R V 61MP (nguon: Sony official) https://www.sony.com/en/interchangeable-lens-cameras/ilce-7rm5
DPReview https://www.dpreview.com/reviews/sony-a7r-v
"""
    res = citation_checker(text)
    assert res["total_links"] == 2
    assert res["tier1_count"] >= 1
    print(f"test_citation_checker PASS tier1={res['tier1_count']}")

def test_citation_checker_no_links():
    from sony_alpha_viet.blog.citation_checker import citation_checker
    res = citation_checker("Bai khong co link nao, 61MP rat cao")
    assert res["total_links"] == 0
    assert res["score"] == 0
    print("test_citation_checker_no_links PASS")

def test_freshness_check_old_price():
    from sony_alpha_viet.blog.freshness_check import freshness_check
    old = "Sony A7 IV gia 60 trieu, bai viet 2024, firmware 1.0"
    res = freshness_check(old)
    assert res["freshness_score"] <= 60
    assert len(res["issues"]) >= 1
    print(f"test_freshness_old PASS score={res['freshness_score']}")

def test_freshness_check_fresh():
    from sony_alpha_viet.blog.freshness_check import freshness_check
    fresh = """
# Sony A7 IV review

Cap nhat 11/2026: Gia hien tai 52tr body tai Sony VN, firmware 2.02 them Focus Bracketing.

Bai viet 2026.
"""
    res = freshness_check(fresh)
    assert res["freshness_score"] >= 80
    assert res["has_2026_update"] is True
    print(f"test_freshness_fresh PASS score={res['freshness_score']}")

def test_brand_voice_checker_pass():
    from sony_alpha_viet.blog.brand_voice_checker import brand_voice_checker
    sample = (
        "Sony A7 IV với cảm biến Exmor R do Sony tự phát triển, sensor số 1 thế giới. "
        "Hệ sinh thái ngàm E nhỏ gọn hơn 200 lens cho mọi nhu cầu. "
        "Mang đến trải nghiệm KANDO cân bằng giữa tốc độ và độ phân giải. "
        "Dù 4K60 crop 1.5x để đảm bảo nhiệt độ, giải pháp trong hệ E-mount là A7S III. "
        "Chọn Sony không chỉ chọn máy, mà chọn hệ sinh thái E-mount nhỏ gọn tạo KANDO."
    )
    res = brand_voice_checker(sample)
    assert res["brand_score"] == 100
    assert "✅" in res["verdict"]

def test_brand_voice_checker_missing():
    from sony_alpha_viet.blog.brand_voice_checker import brand_voice_checker
    bad = "Máy ảnh chụp đẹp, có crop nhưng đối thủ tốt hơn Sony rất nhiều."
    res = brand_voice_checker(bad)
    assert res["brand_score"] < 60

if __name__ == "__main__":
    test_aio_audit_has_tldr()
    test_aio_audit_missing_tldr()
    test_paa_generator()
    test_citation_checker_with_links()
    test_citation_checker_no_links()
    test_freshness_check_old_price()
    test_freshness_check_fresh()
    print("All tests PASS")
