#!/usr/bin/env python3
"""Apply the term and wording decisions from the 25/11/2026 "All Terms" sheet review to a data directory.

The public sample is updated in the same commit as this script. Run it once more on the private data,
otherwise the next `scripts/publish.sh` export brings the old terms back into data-sample/:
    uv run python scripts/migrate_2026_11_25.py data-sample
    uv run python scripts/migrate_2026_11_25.py "$SONY_VN_DATA"
Running it twice changes nothing the second time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DAY = "25/11/2026"
STAMP = "2026-11-25T00:00:00"
SOURCE = "all-terms-2026-11-25"

# Locked terms the user re-decided, and unlocked terms from the Sony trainers' column D.
UPDATE = {
    "Recording Media": {"vi": "thẻ ghi", "short": "thẻ ghi", "locked": True,
                        "note": f"Duyệt {DAY}. Memory Card, Media, Rec. Media Settings vẫn là thẻ nhớ. Cấm 'phương tiện ghi hình'."},
    "Preset": {"note": f"Đứng riêng giữ tiếng Anh; tên tính năng ghép dịch 'đặt trước' (duyệt {DAY})."},
    "Preset Focus": {"vi": "lấy nét đặt trước", "short": "lấy nét đặt trước", "locked": True, "note": f"Duyệt {DAY}."},
    "Preset Focus/Zoom": {"vi": "lấy nét/zoom đặt trước", "short": "lấy nét/zoom đặt trước", "locked": True,
                          "note": f"Duyệt {DAY}."},
    "Developer Tools": {"vi": "công cụ nhà phát triển", "short": "công cụ nhà phát triển", "locked": True,
                        "note": f"Duyệt {DAY}. Active = 'Hoạt động'."},
    "My Dial": {"vi": "vòng xoay của tôi", "short": "vòng xoay của tôi", "locked": True, "note": f"Duyệt {DAY}."},
    "Mass Storage": {"vi": "Mass Storage", "short": "Mass Storage", "locked": True,
                     "note": f"Giữ tiếng Anh (duyệt {DAY})."},
    "Program Auto": {"vi": "chương trình tự động", "short": "chương trình", "note": f"Mode P (duyệt {DAY})."},
    "Red Eye Reduction": {"vi": "giảm đỏ mắt", "short": "giảm đỏ mắt", "note": f"Duyệt {DAY}."},
    "Playback": {"note": "âm thanh ghi chú thoại: 'phát'. Được dùng 'tốc độ phát lại' (quay chuyển động chậm) và "
                         "'phát lại' âm thanh ghi chú thoại."},
}

# New terms decided in the review (not in the glossary before). (en, vi, short, locked, note)
NEW = [
    ("Preset White Balance", "cân bằng trắng đặt trước", None, True, f"Duyệt {DAY}."),
    ("Identification Target", "đối tượng nhận diện", None, False, "Khác Recognition Target (nhận dạng)."),
    ("REC Lamp", "đèn ghi hình", None, False, None),
    ("Rec. Media dur HDMI Output", "ghi thẻ khi xuất HDMI", None, False, "Recording Media during HDMI Output."),
    ("Release w/o Lens", "chụp không ống kính", None, False, None),
    ("Anti Motion Blur", "chống nhòe chuyển động", None, False, None),
    ("Gamma Display Assist", "hỗ trợ hiển thị Gamma", None, False, None),
    ("Bright Monitoring", "tăng sáng Live View", None, False, None),
    ("Focus Map", "bản đồ lấy nét", None, False, None),
    ("USB Streaming", "truyền phát USB", None, False, None),
    ("Network Streaming", "truyền phát mạng", None, False, None),
    ("Auto Framing", "tự động căn khung", None, False, None),
    ("Framing Stabilizer", "ổn định căn khung", None, False, None),
    ("Cnt Shoot Speed Boost", "tăng tốc chụp liên tục", None, False, "Continuous Shooting Speed Boost."),
    ("Composite RAW Sht.", "chụp RAW tổng hợp", None, False, None),
    ("NR Shooting", "chụp giảm nhiễu", None, False, None),
    ("Shooting for HDR", "chụp HDR", None, False, None),
    ("Exp. Value Expand", "mở rộng giá trị phơi sáng", None, False, None),
    ("Button Navigator", "hướng dẫn nút", None, False, None),
    ("Footer", "thanh dưới", None, False, "Footer Custom = tùy chỉnh thanh dưới."),
    ("Volume Photography Commands", "lệnh chụp ảnh số lượng lớn", None, False, None),
    ("Scan and Tag", "quét và gắn thẻ", None, False, None),
    ("In-camera Photo Cropping", "cắt ảnh trong máy", None, False, None),
    ("Dual Gain Shooting", "chụp độ lợi kép", None, False, None),
    ("Star Shooting Mode", "chế độ chụp sao", None, False, None),
    ("Device Certificate", "chứng chỉ thiết bị", None, False, "C2PA."),
    ("User Certificate", "chứng chỉ người dùng", None, False, "C2PA."),
    ("Fingerprint", "fingerprint", None, False, "Của chứng chỉ; không dịch 'vân tay'."),
    ("Color Invert", "đảo màu", None, False, None),
    ("Color Correction", "hiệu chỉnh màu", None, False, None),
    ("High Contrast", "tương phản cao", None, False, None),
    ("Exposure Assist", "hỗ trợ phơi sáng", None, False, None),
    ("AWB Transition Speed", "tốc độ chuyển AWB", None, False, None),
    ("Action for No Rangefind", "khi không bắt được nét", None, False, None),
]

# Help-text wording the review settled on. Python regex, applied by the engine as autofix.
SUBSTITUTIONS = [
    (r"Không hợp lệ (với|ở|khi|vì|do|trong) ", r"Không khả dụng \1 ", "Invalid = không khả dụng"),
    (r"Nhấn và giữ", "Nhấn giữ", None),
    (r"nhấn nút chụp xuống một nửa", "nhấn nửa nút chụp", None),
    (r"chụp theo khoảng thời gian", "chụp cách quãng", "Interval Shooting = chụp cách quãng"),
    (r"Không thể thực hiện được\.", "Không thể thực hiện.", None),
    (r"nếu không có thao tác nào được thực hiện trong vòng", "khi không có thao tác trong", None),
    (r"khi không hoạt động sau (\d+ (?:giây|phút))", r"khi không có thao tác trong \1", None),
    (r"Xoá", "Xóa", "dấu thanh kiểu mới"),
    (r"xoá", "xóa", "dấu thanh kiểu mới"),
    (r"phần mềm đặc biệt", "phần mềm chuyên dụng", None),
    (r"Chiếu đèn flash", "Nháy đèn flash", None),
    (r"chiếu đèn flash", "nháy đèn flash", None),
    (r"trong khi xem lại", "khi xem lại", None),
    (r"Có thể thực hiện (khi|nếu)", r"Dùng được \1", None),
    (r"Sử dụng một thẻ nhớ", "Hãy dùng thẻ nhớ", None),
    (r"Được sử dụng khi", "Dùng khi", None),
    (r"Chạy một ứng dụng hỗ trợ", "Hãy chạy ứng dụng hỗ trợ", None),
    (r"Tự động chương trình", "Chương trình tự động", "Program Auto (duyệt 25/11/2026)"),
    (r"đã chỉ định cho", "đã gán cho", "Assign = gán"),
    (r"^Chỉ định ", "Gán ", "Assign = gán"),
    (r"^Vô hiệu hóa ", "Tắt ", None),
    (r"CF express", "CFexpress", "tên chuẩn"),
    (r"ở giá trị (\d+(?:\.\d+)?p)", r"ở \1", None),
    (r"khi máy được khởi chạy", "khi khởi động máy", None),
    (r"ngày-giờ", "ngày giờ", None),
    (r"Ngày-giờ", "Ngày giờ", None),
    (r"ảnh được lọc", "ảnh đã lọc", None),
    (r"thiết bị được kết nối", "thiết bị đã kết nối", None),
    (r"Kích thước của vùng lấy nét", "Kích thước vùng lấy nét", None),
    (r"Mặc dù được biểu thị bằng số nguyên nhưng tốc độ khung hình thực tế là",
     "Dù hiển thị dạng số nguyên, tốc độ khung hình thực tế là", None),
    (r"chứng chỉ số gốc", "chứng chỉ gốc", None),
    (r"chiều dài tiêu cự", "tiêu cự", None),
    (r"([Cc])hứng chỉ cho C2PA", r"\1hứng chỉ C2PA", None),
    (r"\nChuyển sang thẻ nhớ", "\nHãy chuyển sang thẻ nhớ", None),
    (r"này\. Chuyển sang", "này. Hãy chuyển sang", None),
    (r"ngày sau đây", "ngày dưới đây", None),
    (r"^Bật chọn ", "Cho phép chọn ", "Enables selection of = cho phép chọn"),
    (r"([Tt])ốc độ bít", r"\1ốc độ bit", "bit rate"),
    (r"([Tt])iết kiệm điện(?! năng)", r"\1iết kiệm pin", "Power Save = tiết kiệm pin"),
    (r"ID duy nhất được lấy", "ID duy nhất đã thu được", None),
    (r"kiểm chứng", "xác minh", None),
    (r" theo ngày này", " của ngày này", None),
    (r"Hãy tìm dịch vụ sửa chữa\.", "Vui lòng mang máy đi sửa chữa.", None),
    (r"Chức năng này hiện đang bị (?:vô hiệu hóa|tắt)\.", "Chức năng này hiện đang tắt.", None),
    (r"Bạn có thể xóa cờ đoạn phim bằng cách nhấn nút hai lần\.", "Nhấn nút hai lần để xóa cờ đoạn phim.", None),
    # "higher than <card>" = from <card> up; keeps the line break where the original had one
    (r"cao\nhơn (SDXC\s+[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*(?:\s+hoặc\s+(?:thẻ nhớ\s+)?CFexpress\s+VPG\d+)?|CFexpress\s+VPG\d+)",
     r"từ\n\1 trở lên", "higher than <thẻ> = từ <thẻ> trở lên"),
    (r"cao hơn\n(SDXC\s+[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*(?:\s+hoặc\s+(?:thẻ nhớ\s+)?CFexpress\s+VPG\d+)?|CFexpress\s+VPG\d+)",
     r"từ\n\1 trở lên", "higher than <thẻ> = từ <thẻ> trở lên"),
    (r"cao hơn (SDXC\s+[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*(?:\s+hoặc\s+(?:thẻ nhớ\s+)?CFexpress\s+VPG\d+)?|CFexpress\s+VPG\d+)",
     r"từ \1 trở lên", "higher than <thẻ> = từ <thẻ> trở lên"),
]

# Older substitutions that now contradict a decision above.
DISABLE = {"Mass Storage": f"Mass Storage giữ tiếng Anh (người dùng duyệt {DAY})"}
# Words the sheet keeps on purpose: Mass Storage (decision above), fingerprint (certificate),
# webcam (loanword like Vlog), low pass (trainer Sony: "Bộ lọc low pass").
EXCEPTIONS_ADD = (("standards", "Mass Storage"), ("loanwords", "fingerprint"), ("loanwords", "webcam"),
                  ("loanwords", "low pass"))

PLAYBACK_BANNED ="(?<!tốc độ )[Pp]hát lại(?! âm thanh)(?! với ảnh đã có ghi chú thoại)"

RULES_MD_REPLACE = {
    "- Mass Storage = **Lưu trữ**": f"- Mass Storage = **Mass Storage** (giữ tiếng Anh, duyệt {DAY})",
    "- My Dial = **Đĩa xoay của tôi**": f"- My Dial = **Vòng xoay của tôi** (duyệt {DAY})",
}
RULES_MD_SECTION = f"""
### 11. HELP TEXT VÀ THÔNG BÁO (duyệt {DAY}, bảng All Terms)
- Mô tả mục bật/tắt: **Chọn có … hay không.** Nhãn chuyển nhanh: **Bật/tắt …**; nhãn giữ nút: **… khi nhấn giữ**, giữ một lần: **… khi nhấn**
- Invalid = **Không khả dụng**; Available when… = **Dùng được khi…**; câu yêu cầu người dùng làm gì mở bằng **Hãy …**
- Enables selection of X = **Cho phép chọn X**; Assign = **gán**; Failed (trong câu) = **không thành công**
- Thẻ nhớ "higher than SDXC V60" = **từ SDXC V60 trở lên**
- Recording Media = **Thẻ ghi**; Memory Card / Rec. Media Settings = **thẻ nhớ / cài đặt thẻ nhớ**
- Preset đứng riêng giữ **Preset**; tên tính năng ghép dịch **đặt trước** (Lấy nét/Zoom đặt trước, Cân bằng trắng đặt trước)
"""


def _load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _save(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def migrate(data: Path) -> dict:
    report = {"glossary_updated": 0, "glossary_added": 0, "rules_added": 0, "rules_disabled": 0, "banned_updated": 0,
              "keep_english_updated": 0, "exceptions_added": 0, "rules_md_updated": False}

    gpath = data / "glossary.json"
    glossary = _load(gpath, [])
    by_en = {g["en"].lower(): g for g in glossary}
    for en, fields in UPDATE.items():
        entry = by_en.get(en.lower())
        if entry is None:
            entry = {"en": en, "vi": fields.get("vi", en), "category": SOURCE}
            glossary.append(entry)
            by_en[en.lower()] = entry
        before = dict(entry)
        entry.update(fields)
        report["glossary_updated"] += entry != before
    for en, vi, short, locked, note in NEW:
        if en.lower() in by_en:
            continue
        entry = {"en": en, "vi": vi, "short": short or vi, "category": SOURCE}
        if locked:
            entry["locked"] = True
        if note:
            entry["note"] = note
        glossary.append(entry)
        by_en[en.lower()] = entry
        report["glossary_added"] += 1
    glossary.sort(key=lambda g: g["en"].lower())
    _save(gpath, glossary)

    rpath = data / "rules.json"
    rules = _load(rpath, {"substitutions": [], "exact": {}, "banned": []})
    have = {s["pattern"] for s in rules["substitutions"]}
    n = sum(1 for s in rules["substitutions"] if str(s.get("id", "")).startswith("t25"))
    for pattern, replace, note in SUBSTITUTIONS:
        if pattern in have:
            continue
        rule = {"id": f"t25{n:02d}", "pattern": pattern, "replace": replace, "fallback": None, "source": SOURCE,
                "added": STAMP, "hits": 0, "count": 0}
        if note:
            rule["note"] = note
        rules["substitutions"].append(rule)
        n += 1
        report["rules_added"] += 1
    for s in rules["substitutions"]:
        if s["pattern"] in DISABLE and not s.get("disabled"):
            s["disabled"] = True
            s["disabled_why"] = DISABLE[s["pattern"]]
            report["rules_disabled"] += 1
    for b in rules.get("banned", []):
        if b["pattern"] == "[Pp]hát lại":
            b["pattern"] = PLAYBACK_BANNED
            b["why"] = "Playback = xem lại (trừ 'tốc độ phát lại' và phát lại âm thanh ghi chú thoại, duyệt 25/11/2026)"
            report["banned_updated"] += 1
    _save(rpath, rules)

    kpath = data / "keep_english.json"
    keep = _load(kpath, [])
    for k in keep:
        if k.get("term") == "Preset" and "đặt trước" in k.get("vi_variants", {}):
            del k["vi_variants"]["đặt trước"]
            k["why"] += f". Tên tính năng ghép dịch 'đặt trước' (Preset Focus/Zoom, Preset White Balance; duyệt {DAY})"
            k["updated"] = STAMP
            report["keep_english_updated"] += 1
    _save(kpath, keep)

    epath = data / "exceptions.json"
    exceptions = _load(epath, {})
    for group, term in EXCEPTIONS_ADD:
        items = exceptions.setdefault(group, [])
        if term not in items:
            items.append(term)
            report["exceptions_added"] += 1
    _save(epath, exceptions)

    mpath = data / "rules.md"
    if mpath.exists():
        text = mpath.read_text(encoding="utf-8")
        new = text
        for old, rep in RULES_MD_REPLACE.items():
            new = new.replace(old, rep)
        if "### 11. HELP TEXT" not in new:
            new = new.rstrip("\n") + "\n" + RULES_MD_SECTION
        if new != text:
            mpath.write_text(new, encoding="utf-8")
            report["rules_md_updated"] = True
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("data", type=Path, help="data directory (data-sample or $SONY_VN_DATA)")
    print(json.dumps(migrate(ap.parse_args().data), ensure_ascii=False))
