"""Trainer knowledge base: search, get, add, tree against data-sample/knowledge."""


def test_search_accent_insensitive_and_alias(env):
    from sony_alpha_viet import knowledge
    assert knowledge.search("khau do")[0]["title"] == "Khẩu độ"
    assert knowledge.search("Aperture")[0]["title"] == "Khẩu độ"
    assert knowledge.search("zzzz") == []
    assert all(r["section"] != "Liên quan" for r in knowledge.search("khẩu độ", 20))


def test_get_by_title_path_and_suggestions(env):
    from sony_alpha_viet import knowledge
    assert knowledge.get("khẩu độ")["path"] == "1 Kiến thức/Phơi sáng/Khẩu độ.md"
    assert knowledge.get("1 Kiến thức/Phơi sáng/Khẩu độ")["title"] == "Khẩu độ"
    miss = knowledge.get("Khau")
    assert "error" in miss and "Khẩu độ" in miss["suggestions"]


def test_add_appends_to_section_and_creates_note(env):
    from sony_alpha_viet import knowledge
    r = knowledge.add("Khẩu độ", "- *F1.4 có nét không?* Có, nếu lấy nét đúng mắt.")
    text = knowledge.get("Khẩu độ")["text"]
    assert r["created"] is False and "## Câu hỏi học viên hay hỏi" in text and "F1.4 có nét không?" in text
    assert text.count("## Câu hỏi học viên hay hỏi") == 1
    r = knowledge.add("1 Kiến thức/Màu sắc/Cân bằng trắng", "Đặt K thấp → ảnh xanh hơn.", section="Hiểu nhanh")
    assert r["created"] and "## Hiểu nhanh" in knowledge.get("Cân bằng trắng")["text"]
    assert "error" in knowledge.add("../ngoài", "x") and "error" in knowledge.add("/tmp/x", "x")


def test_tree_shape(env):
    from sony_alpha_viet import knowledge
    t = knowledge.tree()
    assert t["count"] == 2
    assert t["1 Kiến thức"]["Phơi sáng"]["_notes"][0]["title"] == "Khẩu độ"
    assert t["2 Giáo án"]["_notes"][0]["path"].startswith("2 Giáo án/")
