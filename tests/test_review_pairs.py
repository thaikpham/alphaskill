import re
import zipfile
import xml.dom.minidom

from sony_alpha_viet.xls import review_pairs as rp

ROWS = [
    {"file": "a.xls", "row": 3, "sid": "S1", "en": "Shutter", "vi": "Chụp", "an": "Màn trập"},
    {"file": "b.xls", "row": 9, "sid": "S2", "en": "Shutter", "vi": "Chụp", "an": "Màn trập"},  # duplicate pair
    {"file": "a.xls", "row": 4, "sid": "S3", "en": "Shutter", "vi": "Màn trập ngắn", "an": ""},  # same EN, other VI
    {"file": "a.xls", "row": 5, "sid": "S4", "en": "Hawaii", "vi": "Hawaii", "an": ""},  # kept English
    {"file": "a.xls", "row": 6, "sid": "S5", "en": "<cE660>A & B\r\nC", "vi": "x", "an": "<cE660>A & B\nC\x07"},
]


def test_build_pairs_dedups_and_prefers_an():
    tabs = rp.build_pairs(ROWS)
    todo, keep = tabs[rp.TAB_TODO], tabs[rp.TAB_KEEP]
    assert [(t["en"], t["vi"]) for t in todo][:2] == [("Shutter", "Màn trập"), ("Shutter", "Màn trập ngắn")]
    assert todo[0]["rows"] == [["a.xls", 3, "S1"], ["b.xls", 9, "S2"]]
    assert [t["sheet_row"] for t in todo] == [2, 3, 4]
    assert [(t["en"], t["rows"][0][2]) for t in keep] == [("Hawaii", "S4")]
    assert sum(len(t["rows"]) for v in tabs.values() for t in v) == len(ROWS)


def test_write_xlsx_is_wellformed_and_keeps_text(tmp_path):
    tabs = rp.build_pairs(ROWS)
    out = tmp_path / "review.xlsx"
    rp.write_xlsx(out, tabs)
    with zipfile.ZipFile(out) as z:
        for name in z.namelist():
            xml.dom.minidom.parseString(z.read(name))  # every part parses
        wb = z.read("xl/workbook.xml").decode()
        assert rp.TAB_TODO in wb and rp.TAB_KEEP in wb
        sheet1 = z.read("xl/worksheets/sheet1.xml").decode()
    cells = re.findall(r'<t xml:space="preserve">(.*?)</t>', sheet1, re.S)
    assert cells[:2] == ["English", "Vietnamese"]
    assert "&lt;cE660&gt;A &amp; B\nC" in cells  # token, ampersand and line break kept, control char dropped
    assert len(cells) == 2 * (len(tabs[rp.TAB_TODO]) + 1)
