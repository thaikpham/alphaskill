"""
tests/test_blog_audit.py - blog_audit (chấm 40 tiêu chí một lượt) và ca hồi quy của brand, freshness, citation, entity.
Chạy: uv run pytest tests/test_blog_audit.py -q
Không cần internet: citation dùng check_links=False. Fixture không tồn tại thì test FAIL (không skip).
"""

import re
from pathlib import Path

from sony_alpha_viet.blog import seo_audit
from sony_alpha_viet.blog._doc import as_article, band
from sony_alpha_viet.blog.aio_audit import aio_audit, check_entity, check_faq, check_sourced_numbers, check_table
from sony_alpha_viet.blog.audit import _from_links, blog_audit
from sony_alpha_viet.blog.brand_voice_checker import brand_voice_checker, check_kando, check_no_competitor_win
from sony_alpha_viet.blog.citation_checker import citation_checker
from sony_alpha_viet.blog.freshness_check import freshness_check

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "skills" / "sony-alpha-viet" / "examples" / "example-blog-post.md"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "howto-article.md"

ANSWER = (
    "Khoảng 580 shot mỗi lần sạc theo công bố của Sony trong điều kiện thử nghiệm chuẩn. "
    "Khi chụp cưới kéo dài cả buổi, nên mang thêm một hoặc hai pin dự phòng, vì nhiệt độ ngoài trời "
    "và việc dùng màn hình nhiều sẽ làm pin hao nhanh hơn."
)
FAQ_BOLD = """## FAQ

### Pin A7 IV dùng được bao lâu?
**Khoảng 580 shot mỗi lần sạc** theo công bố của Sony trong điều kiện thử nghiệm chuẩn. Khi chụp cưới kéo dài cả buổi, nên mang thêm một hoặc hai pin dự phòng, vì nhiệt độ ngoài trời và việc dùng màn hình nhiều sẽ làm pin hao nhanh hơn.

### Có cần IBIS không?
**Có**, IBIS 5 trục giúp chụp chậm ổn định hơn khi thiếu sáng, nhờ đó giữ được chi tiết mà không cần tăng ISO quá cao. Với ảnh tĩnh cần độ chi tiết tối đa, vẫn nên dùng chân máy, vì IBIS bù rung tay chứ không đứng yên hoàn toàn thay chân máy.

### Có chống bụi không?
**Có**, thân máy có gioăng chống bụi và ẩm ở mức nhất định theo thông số của Sony. Tuy vậy, khi đi mưa hoặc chụp ở nơi nhiều cát, nên bảo quản máy trong túi và lau khô ống kính sau mỗi buổi để giữ máy bền lâu.
"""
TLDR_BULLETS = (
    "# Sony A7 IV\n\nTL;DR:\n- Chọn A7 IV cho cưới nhờ pin 580 shot.\n- File 33MP nhẹ, xử lý nhanh.\n"
    "- Giá dễ tiếp cận cho người mới.\n\n## Mục\nNội dung."
)
BASE = (
    "---\ntitle: Sony A7 IV\nprimary_keyword: Sony A7 IV\n---\n\n# Sony A7 IV có tốt không?\n\n"
    "TL;DR: A7 IV là lựa chọn cân bằng cho người chụp cưới và chân dung, với 33MP, pin 580 shot và Eye AF.\n\n"
    "## Cảm biến\nCảm biến Exmor do Sony tự phát triển, sensor số 1 thế giới theo Sony official.\n\n"
    "Trạng thái giá: [cần xác minh] trên sony.com.vn.\n"
)


def _failed(res, cid):
    return [f for f in res["failed"] if f["id"] == cid]


def _manual(res, cid):
    return [m for m in res["manual_review"] if m["id"] == cid]


def _item(res, criterion):
    return next(i for i in res["items"] if i["criterion"] == criterion)


def _expected_verdict(res):
    """Band theo điểm, nhưng tiêu chí bắt buộc fail thì không được Đạt."""
    v = band(res["overall_score"])
    return "Cần sửa" if res["required_failed"] and v == "Đạt" else v


def test_competitor_better_fails_39():
    text = "Canon tốt hơn Sony về ảnh tĩnh."
    assert check_no_competitor_win(text)["pass"] is False
    hits = _failed(blog_audit(text), 39)
    assert hits and "Canon tốt hơn Sony" in hits[0]["quote"]


def test_sony_worse_than_competitor_fails_39():
    res = check_no_competitor_win("Sony kém hơn Canon về AF.")
    assert res["pass"] is False and not res.get("manual")


def test_sony_limitation_without_alternative_is_manual_39():
    res = check_no_competitor_win("Máy bị crop khi quay 4K60 trong thời gian dài.")
    assert res["pass"] is False and res["manual"] is True
    assert "người duyệt" in res["evidence"]


def test_sony_limitation_with_in_ecosystem_alternative_passes_39():
    text = "Máy bị crop khi quay 4K60. Cần không crop, chọn A7S III trong cùng hệ E-mount."
    assert check_no_competitor_win(text)["pass"] is True


def test_crop_as_technique_does_not_flag_39():
    assert check_no_competitor_win("Chụp crop sâu cho ảnh chim. Cần crop sâu khi lấy nét xa.")["pass"] is True


def test_sony_vs_sony_does_not_fail_39():
    text = "Sony A7 IV tốt hơn Sony A7 III về AF. Sony A7 III kém hơn A7 IV về độ phân giải."
    assert check_no_competitor_win(text)["pass"] is True


def test_brand_manual_blocks_chuan_sony_verdict():
    text = (
        "# Sony A7 IV\n\n"
        "Cảm biến Exmor do Sony tự phát triển, là sensor số 1 thế giới.\n\n"
        "Hệ ngàm E có hơn 200 ống kính cho mọi máy.\n\n"
        "Mang đến trải nghiệm KANDO khi chụp cưới.\n\n"
        "Máy bị crop khi quay 4K60 trong thời gian dài.\n\n"
        "Chọn Sony không chỉ chọn máy, mà chọn hệ sinh thái E-mount nhỏ gọn, triết lý cân bằng, và hành trình tạo KANDO.\n"
    )
    res = brand_voice_checker(text)
    assert res["brand_score"] == 100
    assert "Chuẩn Sony" not in res["verdict"] and "người duyệt" in res["verdict"]


def test_can_bang_trang_does_not_satisfy_38():
    assert check_kando("Chỉnh cân bằng trắng cho ảnh cưới.")["pass"] is False
    assert check_kando("Đây là sự cân bằng Sony tính toán.")["pass"] is True


def test_freshness_follows_today():
    text = "# Sony A7 IV\n\nCập nhật 11/2026: Xác minh giá và thông số trên sony.com.vn\n\nBài viết 2026."
    fresh = freshness_check(text, today="2026-11-11")
    stale = freshness_check(text, today="2028-01-01")
    assert fresh["freshness_score"] >= 80 and fresh["has_current_update"] is True
    assert stale["freshness_score"] < 80 and stale["has_current_update"] is False


def test_tldr_three_bullets_counted_same_by_seo_and_aio():
    seo_item = next(i for i in seo_audit(TLDR_BULLETS, "Sony A7 IV")["items"] if i["id"] == 6)
    aio_item = next(i for i in aio_audit(TLDR_BULLETS, "Sony A7 IV")["items"] if i["criterion"] == 11)
    assert seo_item["status"] == "Chưa đạt" and aio_item["pass"] is False
    seo_words = re.search(r"(\d+) từ", seo_item["evidence"]).group(1)
    aio_words = re.search(r"(\d+) từ", aio_item["evidence"]).group(1)
    assert seo_words == aio_words == "22"
    assert "3 bullet" in seo_item["evidence"] and "3 bullet" in aio_item["evidence"]


def test_task_list_lines_do_not_count_as_paragraph_for_7():
    body = "Mở đầu ngắn.\n- [ ] Bước một. Hai. Ba. Bốn. Năm.\n- [ ] Bước hai. Hai. Ba. Bốn. Năm.\n"
    item = next(i for i in seo_audit(f"# Bài\n\n{body}")["items"] if i["id"] == 9)
    assert item["status"] == "Đạt"
    long_p = next(i for i in seo_audit("# Bài\n\nMột. Hai. Ba. Bốn. Năm. Sáu.\n")["items"] if i["id"] == 9)
    assert long_p["status"] == "Một phần"


def test_faq_answer_with_bold_passes_14():
    res = check_faq(FAQ_BOLD)
    assert res["pass"] is True, res["evidence"]
    assert "FAQ 3 câu" in res["evidence"]


def test_seven_question_faq_fails_14():
    faq = "## FAQ\n\n" + "".join(f"### Câu hỏi số {i}?\n{ANSWER}\n\n" for i in range(1, 8))
    res = check_faq(faq)
    assert res["pass"] is False and "7 câu" in res["evidence"]
    assert _failed(blog_audit(faq), 14)


def test_two_by_two_table_fails_15():
    table = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    assert check_table(table)["pass"] is False
    assert _failed(blog_audit(f"# Bài\n\n{table}"), 15)


def test_zv_e10_entity_passes_22():
    text = "Sony ZV-E10 là máy vlog nhỏ gọn. ZV-E10 có micro tốt."
    res = check_entity(text, "Sony ZV-E10")
    assert res["pass"] is True and "zv-e10" in res["evidence"].lower()


def test_sony_com_vn_is_tier1():
    res = citation_checker("Xem [thông số](https://www.sony.com.vn/vi/product/ilce-7m4).", check_links=False)
    assert res["tier1_count"] == 1
    assert "Tier 1" in res["details"][0]["tier"]


def test_unchecked_source_links_go_to_not_checked_29():
    res = blog_audit(BASE + "\nXem [thông số](https://www.sony.com.vn/vi/product/ilce-7m4).\n", today="2026-11-11")
    assert 29 in [x["id"] for x in res["not_checked"]]
    assert 29 not in [f["id"] for f in res["failed"]]


def test_criterion5_counts_links_once_and_skips_code():
    text = ("# Bài\n\nXem [thông số](https://www.sony.com.vn/a), [đánh giá](https://dpreview.com/x). "
            "Thêm https://dpreview.com/x. Đọc [link nội bộ: A7 IV] và [A7 IV](/a7-iv).\n\n"
            "```\nhttps://evil.example/x\n```\n")
    res = _from_links(as_article(text))
    assert res["pass"] is True
    assert res["evidence"] == "internal 2 (cần 2–5), external 2 (cần 1–3)"


def test_criterion5_is_checked_not_na_on_sample():
    res = blog_audit(EXAMPLE.read_text(encoding="utf-8"), "Sony A7 IV hay A7R V", today="2026-11-11")
    assert 5 not in [x["id"] for x in res["not_applicable"]]


def test_h2_meta_opener_and_table_first_fail_12_with_lines():
    text = ("# Bài\n\n## Pin\nTrong phần này, pin dài nhất.\n\n"
            "## Bảng so sánh\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
            "## Pin dài\nPin đạt 580 shot. Dùng thoải mái.\n\n"
            "## FAQ\nTrong phần này, có FAQ.\n")
    item = _item(aio_audit(text), 12)
    assert item["pass"] is False
    assert [h["line"] for h in item["hits"]] == [4, 7]
    assert "Trong phần này" in item["hits"][0]["quote"]


def test_unsourced_number_listed_for_16_as_manual_never_fail():
    text = "## Cảm biến\nCảm biến đạt 33 MP.\n\n## Pin\nTheo Sony, pin 580 shot."
    res = check_sourced_numbers(text)
    assert res["pass"] is False and res["manual"] is True and res["line"] == 2
    assert "33 MP" in res["quote"]
    audit = blog_audit(text)
    assert not _failed(audit, 16)
    hits = _manual(audit, 16)
    assert hits and hits[0]["line"] == 2 and "33 MP" in hits[0]["quote"]


def test_sourced_figure_passes_16():
    assert check_sourced_numbers("## Pin\nTheo Sony, pin đạt 580 shot.\n")["pass"] is True


def test_placeholder_listed_with_line_13():
    res = blog_audit(BASE, today="2026-11-11")
    assert [h["line"] for h in res["placeholders"]] == [13]
    hits = _failed(res, 17)
    assert hits and hits[0]["line"] == 13


def test_placeholder_fix_says_verify_then_replace_not_delete():
    fix = _failed(blog_audit(BASE, today="2026-11-11"), 17)[0]["fix"]
    assert "Sony official" in fix and "không xóa" in fix


def test_no_jsonld_marks_26_and_27_not_applicable():
    res = blog_audit(BASE, today="2026-11-11")
    na = {x["id"]: x["reason"] for x in res["not_applicable"]}
    assert 26 in na and 27 in na
    assert 26 not in [f["id"] for f in res["failed"]]


def test_criterion32_is_not_applicable_derived():
    res = blog_audit(BASE, today="2026-11-11")
    na = {x["id"]: x["reason"] for x in res["not_applicable"]}
    assert na[32] == "derived"
    assert 32 not in [f["id"] for f in res["failed"]]
    assert res["aio_group_score"] == res["groups"]["AIO"]["score"]


def test_required_failure_blocks_dat_verdict():
    res = blog_audit(BASE, today="2026-11-11")
    assert 17 in res["required_failed"] and res["verdict"] != "Đạt"
    assert "17" in res["verdict_reason"]


def test_failed_items_have_no_per_item_booleans_and_locatable_cause_has_quote():
    res = blog_audit(EXAMPLE.read_text(encoding="utf-8"), "Sony A7 IV hay A7R V", today="2026-11-11")
    for f in res["failed"]:
        assert not {"pass", "manual_review", "not_checked", "status"} & set(f)
        assert f["fix"]
        if f["line"]:
            assert f["quote"]
    assert {"failed", "manual_review", "not_applicable", "not_checked", "verdict_reason", "aio_group_score"} <= set(res)


def test_example_post_audit_runs_on_sample():
    assert EXAMPLE.exists(), f"Thiếu ví dụ: {EXAMPLE}"
    res = blog_audit(EXAMPLE.read_text(encoding="utf-8"), "Sony A7 IV hay A7R V", today="2026-11-11")
    assert res["keyword"] == "Sony A7 IV hay A7R V" and res["today"] == "2026-11-11"
    assert res["verdict"] == _expected_verdict(res)
    assert 17 in res["required_failed"]  # ví dụ còn [cần xác minh] trong bảng


def test_howto_fixture_audit_has_groups_and_unique_ids():
    assert FIXTURE.exists(), f"Thiếu fixture: {FIXTURE}"
    res = blog_audit(FIXTURE.read_text(encoding="utf-8"), today="2026-11-11")
    assert set(res["groups"]) == {"SEO", "AIO", "Schema", "Brand"}
    ids = [f["id"] for f in res["failed"]]
    assert len(ids) == len(set(ids))
    assert all("status" not in f for f in res["failed"])
    assert all(x["reason"] for x in res["not_applicable"])
    assert res["verdict"] == _expected_verdict(res)


def test_crlf_bom_frontmatter_matches_lf():
    lf = blog_audit(BASE, today="2026-11-11")
    crlf = blog_audit("﻿" + BASE.replace("\n", "\r\n"), today="2026-11-11")
    assert lf["keyword"] == crlf["keyword"] == "Sony A7 IV"
    assert crlf["overall_score"] == lf["overall_score"]
    assert [f["id"] for f in crlf["failed"]] == [f["id"] for f in lf["failed"]]


def test_bands_80_and_60():
    assert band(80) == "Đạt" and band(79) == "Cần sửa"
    assert band(60) == "Cần sửa" and band(59) == "Thấp"


def test_blog_audit_is_registered_and_not_write_tool():
    from sony_alpha_viet.server import WRITE_TOOLS, mcp
    assert "blog_audit" in mcp._tool_manager._tools
    assert "blog_audit" not in WRITE_TOOLS
