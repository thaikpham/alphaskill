"""Tests for blog module: slugify, style_lint, seo_audit, faq_schema."""
import json
import re
import pytest
from pathlib import Path


@pytest.fixture
def example_post():
    """Load example blog post from skills."""
    example_file = Path(__file__).resolve().parents[1] / "skills" / "sony-alpha-viet" / "examples" / "example-blog-post.md"
    if example_file.exists():
        return example_file.read_text(encoding="utf-8")
    return ""


def test_slugify_basic():
    """Test Vietnamese → slug conversion."""
    from sony_alpha_viet import blog
    assert blog.slugify("Sony A7 IV hay A7R V") == "sony-a7-iv-hay-a7r-v"
    assert blog.slugify("Máy ảnh đẹp") == "may-anh-dep"
    assert blog.slugify("Dấu đích") == "dau-dich"
    # Test max_words
    assert len(blog.slugify("Một hai ba bốn năm sáu bảy", max_words=3).split("-")) <= 3


def test_count_words_basic():
    """Test word counting with markdown parsing."""
    from sony_alpha_viet import blog
    text = "Đây là một bài viết"
    assert blog.count_words(text) == 5
    # Should exclude frontmatter
    text_with_fm = "---\nmeta_title: test\n---\nĐây là một bài viết"
    assert blog.count_words(text_with_fm) == 5
    # Should exclude code fences (Đây là một bài + viết = 5 words, code content excluded)
    text_with_code = "Đây là một bài\n```code\nhai ba bốn\n```\nviết"
    assert blog.count_words(text_with_code) == 5


def test_lookup_prose_term():
    """Test prose term lookup."""
    from sony_alpha_viet import blog
    # Should find glossary entries if skill files exist
    results = blog.lookup_prose_term("Aperture")
    # Results should be a list (may be empty if skill files not available in test env)
    assert isinstance(results, list)


def test_style_lint_basic():
    """Test style linting."""
    from sony_alpha_viet import blog
    text = "Hãy cùng khám phá máy ảnh Sony."
    result = blog.style_lint(text)
    assert "issues" in result
    # Should flag "Hãy cùng khám phá" as AI-sounding
    assert any("ai_sounding" in str(i.get("type", "")) for i in result["issues"])


def test_style_lint_long_sentence():
    """Test detection of long sentences."""
    from sony_alpha_viet import blog
    # Create a sentence > 35 words (need ~36+ words)
    text = "Máy ảnh Sony A7 IV là một chiếc máy rất tốt và có rất nhiều tính năng đặc biệt tuyệt vời mà người chụp ảnh chuyên nghiệp sẽ rất thích và sẽ muốn sử dụng hàng ngày."
    result = blog.style_lint(text)
    assert any("long_sentence" in str(i.get("type", "")) for i in result["issues"]), f"Should flag long sentence, but got: {result['issues']}"


def test_seo_audit_basic():
    """Test SEO audit on basic markdown."""
    from sony_alpha_viet import blog
    markdown = """---
meta_title: "Test Article"
meta_description: "This is a test article about photography"
slug: "test-article"
primary_keyword: "test article"
author: "Test User"
updated: "02/11/2026"
---

# Test Article

**TL;DR:** This is the summary of the article in 50 words or so that explains the main point and gives readers a quick understanding of what they will learn from reading this comprehensive guide.

## Section 1

Some content here with the test article keyword mentioned.

## FAQ

### What is this?
This is a test article about photography and how to use cameras effectively for your work.

### Why test?
Testing is important because it ensures quality and that the test article meets all SEO requirements.

| Item | Value |
|---|---|
| Test | Data |
"""
    result = blog.seo_audit(markdown, primary_keyword="test article")
    assert "score" in result
    assert "items" in result
    # Score should be a ratio like "X/Y"
    assert "/" in result["score"]


def test_seo_audit_example(example_post):
    """Test SEO audit on example blog post."""
    if not example_post:
        pytest.skip("Example post not found")

    from sony_alpha_viet import blog
    result = blog.seo_audit(example_post, primary_keyword="Sony A7 IV hay A7R V")

    assert "score" in result
    assert "items" in result
    assert "required_failed" in result

    # Item 15 đạt: ví dụ không còn [cần xác minh]
    item_15 = next((i for i in result["items"] if i["id"] == 15), None)
    assert item_15 is not None
    assert item_15["status"] == "Đạt"
    assert "[cần xác minh" not in example_post


def test_faq_schema_basic():
    """Test FAQ schema generation."""
    from sony_alpha_viet import blog
    markdown = """---
meta_title: "Test"
meta_description: "Description"
author: "Author Name"
updated: "02/11/2026"
---

# Test Article

## FAQ

### Q1?
Answer one goes here with about fifty words to explain the topic properly and give readers good information about it.

### Q2?
Answer two goes here with about fifty words to explain the second topic and continue the educational content.
"""
    schema_str = blog.faq_schema(markdown)
    assert "<script" in schema_str
    assert "application/ld+json" in schema_str
    assert "Article" in schema_str
    assert "FAQPage" in schema_str
    # Verify valid JSON inside
    import json
    json_match = re.search(r'\{.*\}', schema_str, re.DOTALL)
    assert json_match
    schema_json = json.loads(json_match.group())
    assert "@graph" in schema_json or "@type" in schema_json


def test_seo_audit_example_items(example_post):
    from sony_alpha_viet import blog
    r = blog.seo_audit(example_post)  # keyword read from frontmatter
    st = {i["id"]: i["status"] for i in r["items"]}
    assert st[1] == "Đạt" and st[2] == "Đạt" and st[3] == "Đạt" and st[6] == "Đạt" and st[11] == "Đạt"
    assert st[19] == "Đạt"  # FAQ in article == FAQ in JSON-LD
    assert st[15] == "Đạt" and 15 not in r["required_failed"] and r["complete"]
    assert st[17] == "Đạt"  # placeholder [link nội bộ: …] tính là link nội bộ (3 cái)


def test_faq_schema_roundtrip_and_mismatch(example_post):
    from sony_alpha_viet import blog
    body = example_post.split("```html")[0]
    rebuilt = body + "\n" + blog.faq_schema(body, url="https://example.vn/a", site_name="Example")
    assert next(i for i in blog.seo_audit(rebuilt)["items"] if i["id"] == 19)["status"] == "Đạt"
    tampered = rebuilt.replace("Có. Theo thông số Sony Việt Nam, A7 IV", "Không. Theo thông số Sony Việt Nam, A7 IV", 1)  # edit article FAQ only
    items = {i["id"]: i for i in blog.seo_audit(tampered)["items"]}
    assert items[19]["status"] == "Đạt"  # 19 chỉ kiểm kiểu schema (tiêu chí 26)
    assert items[26]["status"] == "Chưa đạt" and "lệch" in items[26]["evidence"]  # Q/A khớp nguyên văn (tiêu chí 27)
    js = json.loads(re.search(r"\{.*\}", rebuilt.split("<script")[-1], re.S).group())
    art = js["@graph"][0]
    assert art["mainEntityOfPage"] == "https://example.vn/a" and art["publisher"]["name"] == "Example" and art["datePublished"] == "2026-11-11"


def test_faq_multi_paragraph_answer():
    from sony_alpha_viet import blog
    md = "# T\n\n## Câu hỏi thường gặp\n\n### Hỏi?\nĐoạn một.\n\nĐoạn hai.\n\n## Nguồn\n- a\n"
    js = json.loads(re.search(r"\{.*\}", blog.faq_schema(md), re.S).group())
    assert js["@graph"][1]["mainEntity"][0]["acceptedAnswer"]["text"] == "Đoạn một. Đoạn hai."


def test_style_lint_terminology():
    from sony_alpha_viet import blog
    types = {i["type"] for i in blog.style_lint("Máy có cảm biến khung hình đầy đủ và nút màn trập mới.")["issues"]}
    assert "terminology" in types


def test_style_lint_dash_flagged():
    """Test that em/en dashes used as sentence connectors are flagged."""
    from sony_alpha_viet import blog
    text = "Máy ảnh rất mạnh — nó có Eye AF tuyệt vời."
    result = blog.style_lint(text)
    dash_issues = [i for i in result["issues"] if i["type"] == "dash"]
    assert len(dash_issues) > 0, f"Should flag em dash, but got: {result['issues']}"


def test_style_lint_dash_in_code_not_flagged():
    """Test that dashes in code blocks are not flagged."""
    from sony_alpha_viet import blog
    text = "```\nvar x = a — b\n```\nMáy ảnh — công cụ tuyệt vời."
    result = blog.style_lint(text)
    dash_issues = [i for i in result["issues"] if i["type"] == "dash"]
    # Should only flag the one outside code block
    assert len(dash_issues) == 1


def test_style_lint_dash_in_table_not_flagged():
    """Test that dashes in markdown tables are not flagged."""
    from sony_alpha_viet import blog
    text = "| Tiêu chí | Mô tả |\n|---|---|\n| A — B | Kết quả |"
    result = blog.style_lint(text)
    dash_issues = [i for i in result["issues"] if i["type"] == "dash"]
    assert len(dash_issues) == 0, "Should not flag dash in table"


def test_style_lint_not_x_but_y_flagged():
    """Test that 'không phải...mà là' patterns are flagged."""
    from sony_alpha_viet import blog
    text = "Không phải A7 IV yếu, mà là nó có cân bằng khác."
    result = blog.style_lint(text)
    issues = [i for i in result["issues"] if i["type"] == "not_x_but_y"]
    assert len(issues) > 0, f"Should flag 'không phải...mà là', but got: {result['issues']}"


def test_style_lint_not_x_but_y_brand_closer_not_flagged():
    """Test that brand closer 'Chọn Sony không chỉ' is not flagged."""
    from sony_alpha_viet import blog
    text = "Chọn Sony không chỉ chọn máy, mà chọn hệ sinh thái E-mount."
    result = blog.style_lint(text)
    issues = [i for i in result["issues"] if i["type"] == "not_x_but_y"]
    assert len(issues) == 0, "Should not flag brand closer"


def test_style_lint_new_ai_phrase_flagged():
    """Test that new AI-sounding phrases are flagged."""
    from sony_alpha_viet import blog
    text = "Hãy cùng tìm hiểu về máy ảnh Sony A7 IV."
    result = blog.style_lint(text)
    ai_issues = [i for i in result["issues"] if i["type"] == "ai_sounding"]
    assert len(ai_issues) > 0, f"Should flag 'Hãy cùng tìm hiểu', but got: {result['issues']}"


# Regression tests for security fixes (Task 5)

def test_classify_domain_exact_match():
    """Exact host or subdomain match for domain classification."""
    from sony_alpha_viet.blog.citation_checker import classify_domain
    assert "Tier 1" in classify_domain("https://www.sony.com/x")
    assert "Tier 1" in classify_domain("https://imaging-edge.sony.net/page")
    assert "Tier 1" not in classify_domain("https://notsony.com")
    assert "Tier 1" not in classify_domain("https://sony.com.evil.io")


def test_check_link_alive_refuses_private_ips():
    """URL fetch should refuse private, loopback IPs."""
    from sony_alpha_viet.blog.citation_checker import check_link_alive
    import os
    if not os.environ.get("SONY_VN_NO_NET"):
        result = check_link_alive("http://127.0.0.1/")
        assert result["alive"] is None
        assert "Không cho phép" in result["evidence"]


def test_check_link_alive_refuses_non_http():
    """URL fetch should refuse non-http/https schemes."""
    from sony_alpha_viet.blog.citation_checker import check_link_alive
    import os
    if not os.environ.get("SONY_VN_NO_NET"):
        result = check_link_alive("file:///etc/passwd")
        assert result["alive"] is None
        assert "Lược đồ không hỗ trợ" in result["evidence"]


def test_check_link_alive_redirect_allowed(monkeypatch):
    """URL fetch with redirect to public URL is allowed (200 <= 300)."""
    import importlib
    import urllib.error
    import os
    if os.environ.get("SONY_VN_NO_NET"):
        return
    
    cc = importlib.import_module("sony_alpha_viet.blog.citation_checker")
    
    def mock_getaddrinfo(host, port):
        return [(2, 1, 6, '', ('8.8.8.8', 0))]
    
    call_count = [0]
    def mock_open(req, timeout=3):
        call_count[0] += 1
        raise urllib.error.HTTPError(req.full_url, 302, "Found", {"Location": "http://169.254.169.254/"}, None)
    
    monkeypatch.setattr(cc.socket, "getaddrinfo", mock_getaddrinfo)
    monkeypatch.setattr(cc._NO_REDIRECT, "open", mock_open)
    
    result = cc.check_link_alive("http://example.com/")
    assert result["alive"] is True
    assert result["status"] == 302
    assert "169.254.169.254" in result["evidence"]
    assert call_count[0] == 1


def test_colorlab_html_sources_no_href_for_non_http():
    """colorlab_html should render non-http/https sources as plain text."""
    from sony_alpha_viet.blog import colorlab_html
    sources = [
        {"title": "Normal Link", "url": "https://example.com", "publisher": "Example"},
        {"title": "JavaScript URL", "url": "javascript:alert(1)", "publisher": "Evil"}
    ]
    html_output = colorlab_html._sources(sources)
    assert 'href="https://example.com"' in html_output
    assert 'href="javascript:' not in html_output
    assert ">JavaScript URL<" in html_output


def test_colorlab_write_pack_restore_on_gate_failure(tmp_path, monkeypatch):
    """write_pack should restore files if vitest gate fails."""
    from sony_alpha_viet.blog import colorlab
    import subprocess
    
    packs_dir = tmp_path / "src" / "lib" / "lab" / "packs"
    packs_dir.mkdir(parents=True)
    (packs_dir / "index.ts").write_text("import type { Article } from '../types'\n\nexport const PACKS = {}\n")
    
    def mock_run(*args, **kwargs):
        class Result:
            returncode = 1
            stdout = "failed"
            stderr = ""
        return Result()
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    articles = [{"id": "test-1", "title": "Test Article", "kind": "blog"}]
    result = colorlab.write_pack(articles, str(tmp_path), "new-pack", check_gate=True)
    
    assert result.get("restored") is True
    assert not (packs_dir / "new-pack.ts").exists()


def test_server_main_forces_readonly_on_non_loopback(monkeypatch, capsys):
    """server.main() forces read-only for non-loopback hosts."""
    from sony_alpha_viet import server
    import sys
    
    server.PUBLIC = False
    monkeypatch.setattr(sys, "argv", ["prog", "--host", "0.0.0.0"])
    monkeypatch.setattr("sony_alpha_viet.server.mcp.run", lambda: None)
    
    server.main()
    
    assert server.PUBLIC is True
    captured = capsys.readouterr()
    assert "Cảnh báo" in captured.err


def test_style_lint_range_en_dash_not_flagged():
    from sony_alpha_viet import blog
    issues = blog.style_lint("Khẩu F8–F11, tốc độ 5–15s.")["issues"]
    assert not [i for i in issues if i["type"] == "dash"]
