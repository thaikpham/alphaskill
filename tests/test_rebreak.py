from sony_alpha_viet import core
from sony_alpha_viet.xls import agreed as ag

MSG = dict(max_w=453, font_w=27, font_h=36, linefeed="Off")


def test_rebreak_keeps_words_and_slot_line():
    text = "Không thể ghi với cài đặt ghi này.\nHãy chuyển sang thẻ nhớ từ\nSDXC V90 trở lên hoặc thẻ nhớ CFexpress,\nhoặc thay đổi <cE660>cài đặt ghi.\nKhe 2"
    assert core.fit(text, rows=6, **MSG)["verdict"] == "OVER"
    out = core.rebreak(text, rows=6, **MSG)
    assert out and out.split() == text.split()
    assert out.endswith("\nKhe 2") and core.fit(out, rows=6, **MSG)["verdict"] != "OVER"


def test_rebreak_avoids_one_word_lines():
    out = core.rebreak("Chụp sao cho khuôn mặt nằm vừa trong khung.", 300, 29, 38, 2, "Off")
    assert out is None or all(len(line.split()) > 1 for line in out.split("\n"))
    out = core.rebreak("Chụp sao cho khuôn mặt nằm vừa trong khung.", 400, 29, 38, 2, "Off")
    assert out and all(len(line.split()) > 1 for line in out.split("\n"))


def test_rebreak_line_feed_on_drops_manual_breaks():
    text = 'Chưa kết nối mạng.\nNếu dùng Wi-Fi, hãy kiểm tra "Kết nối Wi-Fi"\nđang "Bật".'
    assert core.rebreak(text, 560, 29, 38, 3, "On") == 'Chưa kết nối mạng. Nếu dùng Wi-Fi, hãy kiểm tra "Kết nối Wi-Fi" đang "Bật".'


def test_rebreak_none_when_fits_or_impossible():
    assert core.rebreak("Chưa lắp thẻ nhớ.\nKhe 1", 544, 29, 38, 2, "Off") is None
    assert core.rebreak("Chụp sao cho khuôn mặt nằm vừa trong khung.", 300, 29, 38, 1, "Off") is None


def test_plan_rebreaks_before_flagging_overflow():
    lay = {"max_w": 400, "font_w": 29, "font_h": 38, "rows": 2, "linefeed": "Off"}
    rows = [{"row": 3, "sid": "S50242", "en": "Shoot so the face fits\nin the frame.", "vi": "Chụp ảnh vừa khung",
             "an": "", "au": "", "av": "", "layout": lay}]
    agreed = {"Shoot so the face fits\nin the frame.": {"": "Chụp sao cho khuôn mặt nằm vừa trong khung."}}
    p = ag.plan(rows, agreed)
    x = p["proposals"][0]
    assert p["stats"]["rebroken"] == 1 and p["skipped_width"] == []
    assert "\n" in x["an"] and x["an"].split() == "Chụp sao cho khuôn mặt nằm vừa trong khung.".split()
    assert x["av"].startswith(ag.REBROKEN.strip())
