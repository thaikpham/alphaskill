"""
tests/test_example_post.py - bài ví dụ skills/sony-alpha-viet/examples/example-blog-post.md phải đạt blog_audit.
Chạy: uv run pytest tests/test_example_post.py -q
"""

from pathlib import Path

from sony_alpha_viet.blog import blog_audit, style_lint

EXAMPLE = Path(__file__).resolve().parents[1] / "skills" / "sony-alpha-viet" / "examples" / "example-blog-post.md"
KEYWORD = "Sony A7 IV hay A7R V"


def _text() -> str:
    assert EXAMPLE.exists(), f"Thiếu ví dụ: {EXAMPLE}"
    return EXAMPLE.read_text(encoding="utf-8")


def test_example_post_passes_blog_audit():
    res = blog_audit(_text(), KEYWORD, today="2026-11-11")
    assert res["verdict"] == "Đạt"
    assert res["required_failed"] == []
    assert res["overall_score"] >= 80
    assert not {39, 40} & {f["id"] for f in res["failed"]}


def test_example_post_has_no_unverified_marker():
    assert "[cần xác minh" not in _text()


def test_example_post_style_lint_is_clean():
    assert style_lint(_text())["issues"] == []


def test_example_post_audit_block_matches_tool():
    text = _text()
    res = blog_audit(text, KEYWORD, today="2026-11-11")
    assert f"Điểm tổng: {res['overall_score']}/100, {res['verdict']}" in text
    assert "```text" in text and text.rstrip().endswith("```")
