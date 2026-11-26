from sony_alpha_viet.xls import agreed as ag

WIDE = {"max_w": 2000, "font_w": 27, "font_h": 36, "rows": 3, "linefeed": "Off"}
NARROW = {"max_w": 150, "font_w": 27, "font_h": 36, "rows": 1, "linefeed": "Off"}


def row(n, en, vi, an="", au="", av="", layout=WIDE):
    return {"row": n, "sid": f"S{n}", "en": en, "vi": vi, "an": an, "au": au, "av": av, "layout": layout}


AGREED = {
    "Hold down": {"": "Nhấn giữ"},
    "Delete": {"": "Xóa"},
    "Mass Storage": {"": "Mass Storage"},
    "Shutter": {"Chụp": "Màn trập", "Màn trập ngắn": "Màn trập ngắn"},
    "Anti-flicker Shoot Sel.": {"": "Chọn chụp chống nhấp nháy"},
    "Done": {"": "Đã xong"},
}


def by_row(p):
    return {x["row"]: x for x in p["proposals"]}


def test_new_review2_clear_and_skip():
    rows = [
        row(1, "Hold down", "Nhấn và giữ"),                                   # new proposal
        row(2, "Delete", "Xoá"),                                              # diacritics only
        row(3, "Mass Storage", "Mass Storage", "Lưu trữ", ag.SUGGEST, "Old reason."),  # cleared
        row(4, "Shutter", "Chụp", "Màn trập ngắn", "By a fatal error as photographic terms", "Wrong term."),  # dup EN: AN matches
        row(9, "Shutter", "Chụp"),                                            # dup EN: keyed by current VI
        row(5, "Done", "Đã xong"),                                            # already agreed
        row(6, "Hawaii", "Hawaii"),                                           # no match
    ]
    p = ag.plan(rows, AGREED)
    got = by_row(p)
    assert got[1] == {"row": 1, "sid": "S1", "an": "Nhấn giữ", "au": ag.SUGGEST, "av": "'Nhấn và giữ' → 'Nhấn giữ'."}
    assert got[2]["au"] == ag.SPELLING
    assert got[3] == {"row": 3, "sid": "S3", "an": "", "au": "", "av": ""}
    assert got[9]["an"] == "Màn trập"
    assert 4 not in got and 5 not in got and 6 not in got
    assert p["stats"]["no_match"] == 1 and p["stats"]["already"] == 2


def test_review2_keeps_au_and_appends_av():
    rows = [row(7, "Hold down", "Nhấn và giữ", "Nhấn xuống và giữ", "By a grammatical error", "Word order.")]
    x = ag.plan(rows, AGREED)["proposals"][0]
    assert x["an"] == "Nhấn giữ" and x["au"] == "By a grammatical error"
    assert x["av"] == "Word order. | Review 2: 'Nhấn xuống và giữ' → 'Nhấn giữ'."


def test_overflow_skipped_or_flagged():
    rows = [row(8, "Anti-flicker Shoot Sel.", "Chống nhấp nháy", layout=NARROW)]
    p = ag.plan(rows, AGREED)
    assert p["proposals"] == [] and p["skipped_width"][0]["agreed"] == "Chọn chụp chống nhấp nháy"
    p2 = ag.plan(rows, AGREED, apply_overflow=True)
    assert p2["proposals"][0]["av"].startswith(ag.WIDTH_NOTE)
    assert p2["stats"]["width_flagged"] == 1


def test_reason_long_text_uses_context_and_fallback():
    old = "Thiết lập xem có sử dụng chức năng này hay không.\nNhấn xuống và giữ nút để dùng."
    new = "Chọn có dùng chức năng này hay không.\nNhấn giữ nút để dùng."
    r = ag.reason(old, new)
    assert "→" in r and "Nhấn giữ" in r
    assert ag.reason("a b c d e f g h i j k l m n o p q r s t u v w x y z " * 3 + "\nx",
                     "z y x w v u t s r q p o n m l k j i h g f e d c b a " * 3 + "\ny") == ag.REWORDED


def test_load_agreed_csv(tmp_path):
    f = tmp_path / "agreed.csv"
    f.write_text("English,Vietnamese,AGREED\nShutter,Chụp,Màn trập\nCopy,,Sao chép\n", encoding="utf-8")
    assert ag.load_agreed(f) == {"Shutter": {"Chụp": "Màn trập"}, "Copy": {"": "Sao chép"}}
