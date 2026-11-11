
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

TL;DR: A7 IV tot hon cho tho cuoi vi pin lau 580 shot, file nhe 33MP xu ly nhanh, 2 khe the an toan. A7R V tot hon cho phong canh vi 61MP chi tiet cao nhung file RAW 120MB nang may. Ca hai deu la full-frame ngam E, nen chon theo nhu cau chup chinh cua ban.

Cap nhat 11/2026: thong so theo Sony official, gia tham khao khoang 52 trieu body.

## A7 IV la gi?
A7 IV la may full-frame 33MP ra mat 2021, co IBIS va Eye AF nhan dien mat nguoi (nguon: Sony official). Tho cuoi o HCM dung hai nam van thay rat ben.

## So sanh chi tiet
Bang duoi day tom tat thong so theo cong bo chinh thuc cua Sony.

| Tieu chi | A7 IV | A7R V |
| --- | --- | --- |
| Pin | 580 shot | 530 shot |
| Do phan giai | 33MP | 61MP |

## FAQ

### A7 IV co chong rung khong?
Co, A7 IV co IBIS 5 truc giup chup cam tay o toc do cham ma anh van net. Tho chup tiec trong nha thieu sang thuong dua vao dieu nay de giu toc do an toan ma khong can flash. Khi di chuyen nhieu, ban van nen ket hop gimbal hoac gay chup de anh video on dinh hon.

### Gia A7 IV bao nhieu nam 2026?
Gia tham khao thay doi theo kenh ban va thoi diem, nen kiem tra tren trang san pham chinh thuc cua Sony truoc khi mua. Tai thoi diem cap nhat bai viet, may duoc ban o dang body va kit ong kinh. Neu ngan sach hep, hay can nhac may da qua su dung con bao hanh.

### A7 IV co 2 khe the nho khong?
Co, A7 IV co hai khe the nho gom mot khe CFexpress Type A va mot khe SD UHS-II, giup luu du phong khi quay va chup lien tuc. Tho cuoi thuong ghi file song song vao hai the de an toan du lieu. Nen chon the co toc do ghi du cao de tranh that tiep khi quay video dai.
"""
    res = aio_audit(good, "Sony A7 IV hay A7R V", today="2026-11-11")
    # Sample này phải >=60
    assert res["aio_score"] >= 60, f"Expected >=60, got {res['aio_score']}"
    print(f"test_aio_audit_has_tldr PASS score={res['aio_score']}")

def test_aio_audit_missing_tldr():
    from sony_alpha_viet.blog.aio_audit import aio_audit
    bad = "# Test\n\nNo TLDR, no table, no FAQ"
    res = aio_audit(bad, "A7 IV")
    assert res["aio_score"] < 50
    print("test_aio_audit_missing_tldr PASS")

def test_check_table_with_separator():
    from sony_alpha_viet.blog.aio_audit import check_table
    good = """
| Tieu chi | A7 IV | A7R V |
| --- | --- | --- |
| Pin | 580 shot | 530 shot |
| Do phan giai | 33MP | 61MP |
"""
    res = check_table(good)
    assert res["pass"] is True
    print("test_check_table_with_separator PASS")

def test_check_table_without_separator():
    from sony_alpha_viet.blog.aio_audit import check_table
    bad = "|a|b|c|\n|d|e|f|"
    res = check_table(bad)
    assert res["pass"] is False
    print("test_check_table_without_separator PASS")

def test_check_faq_with_valid_answers():
    from sony_alpha_viet.blog.aio_audit import check_faq
    good = """
## FAQ

**Cau 1?** Co, may nay co IBIS 5 truc 5.5 stop giup chup toc 1 15 s khong rung khi chup tiec toi khong flash. Ky thuat chong rung nay rat quan trong cho tho chup cuoi. Tho chup can nen lua chon may co chong rung tot.

**Cau 2?** May A7 IV khac A7R V o do phan giai chi tiet. A7 IV co 33MP can bang, A7R V co 61MP chi tiet cao nhung file nang. Chon A7 IV neu can xu ly nhanh va file nhe hon. Neu can chi tiet cao chon A7R V.

**Cau 3?** Co, ca hai may deu co 2 khe the nho giup an toan du lieu. The nho la phu kien quan trong dua theo sau may. Cap phim tren 2 the nho giup backup du phong cho du lieu anh video.
"""
    res = check_faq(good)
    assert res["pass"] is True
    print("test_check_faq_with_valid_answers PASS")

def test_check_faq_with_short_answer():
    from sony_alpha_viet.blog.aio_audit import check_faq
    bad = """
## FAQ

**Cau 1?** Co IBIS.

**Cau 2?** Co IBIS.

**Cau 3?** Co IBIS.
"""
    res = check_faq(bad)
    assert res["pass"] is False and "từ" in res["evidence"]
    print("test_check_faq_with_short_answer PASS")

def test_check_faq_with_forbidden_phrase():
    from sony_alpha_viet.blog.aio_audit import check_faq
    bad = """
## FAQ

**Cau 1?** Co may nay co IBIS 5 truc 5.5 stop giup chup toc 1 15 s khong rung khi chup tiec toi khong flash. Chi tiet them xem o tren phan IBIS. Ky thuat nay rat quan trong cho tho chup cuoi.

**Cau 2?** May A7 IV khac A7R V o do phan giai A7 IV 33MP can bang A7R V 61MP chi tiet cao nhung file nang hon. Chon A7 IV neu can xu ly nhanh va cap nhanh. Dieu nay quan trong.

**Cau 3?** Co, ca hai may deu co 2 khe the nho, an toan cho luu tru du phong co backup. The nho la phu kien quan trong dua theo sau may.
"""
    res = check_faq(bad)
    assert res["pass"] is False and "xem o tren" in res["evidence"].lower()
    print("test_check_faq_with_forbidden_phrase PASS")

def test_paa_generator():
    from sony_alpha_viet.blog.paa_generator import paa_generator
    res = paa_generator("Sony A7 IV hay A7R V", "tho chup cuoi")
    assert len(res["paa_questions"]) == 10
    assert "suggestions" in res
    print("test_paa_generator PASS")

def test_paa_hints_no_concrete_numbers():
    from sony_alpha_viet.blog.paa_generator import paa_generator
    res = paa_generator("Sony A7 IV hay A7R V", "tho chup cuoi")
    hint_text = " ".join(s.get("answer_hint", "") for s in res["suggestions"])
    # Check no concrete numbers like 94%, 580 shot, 120MB, 33MP, 61MP
    assert "94%" not in hint_text
    assert "580" not in hint_text
    assert "120MB" not in hint_text
    assert "33MP" not in hint_text
    assert "61MP" not in hint_text
    # Check placeholder usage
    assert "[" in hint_text
    print("test_paa_hints_no_concrete_numbers PASS")

def test_citation_checker_with_links():
    from sony_alpha_viet.blog.citation_checker import citation_checker
    text = """
A7R V 61MP (nguon: Sony official) https://www.sony.com/en/interchangeable-lens-cameras/ilce-7rm5
DPReview https://www.dpreview.com/reviews/sony-a7r-v
"""
    res = citation_checker(text, check_links=False)
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
    import datetime
    today = datetime.date(2026, 11, 5)
    old = "Sony A7 IV gia 60 trieu, bai viet 2024, firmware 1.0"
    res = freshness_check(old, today=today)
    assert res["freshness_score"] <= 60
    assert len(res["issues"]) >= 1
    print(f"test_freshness_old PASS score={res['freshness_score']}")

def test_freshness_check_fresh():
    from sony_alpha_viet.blog.freshness_check import freshness_check
    import datetime
    today = datetime.date(2026, 11, 5)
    fresh = """
# Sony A7 IV review

Cập nhật 11/2026: Xác minh giá và thông số trên sony.com.vn

Bai viet 2026.
"""
    res = freshness_check(fresh, today=today)
    assert res["freshness_score"] >= 80
    assert res["has_current_update"] is True
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
