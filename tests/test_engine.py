"""Engine behaviour on public data-sample (TM rows are seeded per test; no Sony translation memory ships)."""
import json

import pytest


def _seed_tm(tmp_path, rows):
    with open(tmp_path / "data" / "tm.jsonl", "a", encoding="utf-8") as f:
        for i, (en, vi) in enumerate(rows):
            f.write(json.dumps({"id": f"T{i}", "en": en, "vi": vi, "project": "test", "status": "approved-test"}, ensure_ascii=False) + "\n")


@pytest.fixture()
def legacy(env, tmp_path):
    """data-sample rolled back to before the keep_english decisions, with seeded TM rows."""
    core, memory, _ = env
    d = tmp_path / "data"
    (d / "keep_english.json").write_text("[]", encoding="utf-8")
    rules = json.loads((d / "rules.json").read_text(encoding="utf-8"))
    for s in rules["substitutions"]:
        if str(s.get("disabled_why", "")).startswith("keep_english"):
            s.pop("disabled", None); s.pop("disabled_why", None)
    (d / "rules.json").write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")
    gl = json.loads((d / "glossary.json").read_text(encoding="utf-8"))
    old = {"Zoom": "thu phóng", "Digital Zoom": "thu phóng số", "Clear Image Zoom": "thu phóng rõ nét", "Preset": "đặt trước"}
    gl = [g for g in gl if g["en"] != "Time Code"]
    for g in gl:
        if g["en"] in old:
            g["vi"] = g["short"] = old[g["en"]]; g["locked"] = g["en"] == "Zoom"
    (d / "glossary.json").write_text(json.dumps(gl, ensure_ascii=False), encoding="utf-8")
    _seed_tm(tmp_path, [("Zoom", "Thu phóng"), ("Zoom Speed", "Tốc độ thu phóng"), ("Changes the zoom magnification.", "Thay đổi mức thu phóng."),
                        ("Displays the timecode.", "Hiển thị mã thời gian."), ("Preset Name", "Tên đặt trước"),
                        ("Shoots with preset settings.", "Chụp với cài đặt trước."), ("Magnify", "Phóng to")])
    return core, memory, core.Store()


def test_rules_pure_vietnamese(env):
    core, _, s = env
    assert core.apply_rules(s, "Bracket liên tục: 0.3EV 3 ảnh", "Cont. Bracket: 0.3EV 3 Image")["text"] == "Bù trừ liên tục: 0.3EV 3 ảnh"
    assert core.apply_rules(s, "Gửi đến smartphone", "Send to Smartphone")["text"] == "Gửi đến điện thoại"
    assert core.apply_rules(s, "Nút chụp", "Shutter Button")["text"] == "Nút chụp"


def test_audit_flags_sample(env):
    core, _, s = env
    assert any(i["type"] == "banned" for i in core.audit(s, "Recover Image DB", "Khôi phục CSDL ảnh")["issues"])
    assert not core.audit(s, "Exposure Comp.", "Chụp b.trừđộph.s")["ok"]
    assert any(i["type"] == "token_mismatch" for i in core.audit(s, "<cE660>Fan Control", "Điều khiển quạt")["issues"])
    assert any(i["type"] == "english_residue" for i in core.audit(s, "Fan Speed", "Tốc độ fan")["issues"])
    # keep_english ships in data-sample: Zoom/timecode kept, Vietnamese variant flagged
    assert not core.audit(s, "Zoom Speed", "Tốc độ Zoom")["issues"]
    assert not core.audit(s, "Displays the timecode.", "Hiển thị timecode.")["issues"]
    assert any(i["type"] == "keep_english" for i in core.audit(s, "Zoom Speed", "Tốc độ thu phóng")["issues"])


def test_memory_and_learning(env):
    core, memory, s = env
    memory.record_term(s, "Foo Mode", "chế độ foo", note="test")
    assert core.lookup_terms(s, "Foo Mode")[0]["vi"] == "chế độ foo"
    for en in ("Lens Reset", "Lens Reset All"):
        memory.record_feedback(s, en, "Thiết đặt ống kính", "Cài đặt ống kính", reason="test")
    assert core.apply_rules(s, "Thiết đặt màn hình", "Monitor Setting")["text"] == "Cài đặt màn hình"
    assert core.search_tm(s, "Lens Reset")[0]["vi"] == "Cài đặt ống kính"


def test_keep_english_preview_and_apply(legacy):
    core, memory, s = legacy
    plan = memory.keep_english(s, "Zoom", {"thu phóng": "{term}"}, apply=False)
    assert plan["tm_changes"]["count"] == 3
    assert {"r021", "r034"} <= {r["id"] for r in plan["rules_to_disable"]}
    s.reload()
    assert not s.keep and s.gl_by_en["zoom"]["vi"] == "thu phóng"  # preview writes nothing
    memory.keep_english(s, "Zoom", {"thu phóng": "{term}"}, apply=True)
    s.reload()
    assert core.apply_rules(s, "Dải hỗ trợ thu phóng", "Range of Zoom Assist")["text"] == "Dải hỗ trợ Zoom"
    assert core.apply_rules(s, "Thay đổi mức thu phóng.", "Changes the zoom magnification.")["text"] == "Thay đổi mức zoom."
    assert core.search_tm(s, "Zoom Speed")[0]["vi"] == "Tốc độ Zoom"
    assert core.search_tm(s, "Magnify")[0]["vi"] == "Phóng to"  # unrelated rows untouched
    assert s.gl_by_en["digital zoom"]["vi"] == "Zoom số"


def test_keep_english_time_code_and_preset(legacy):
    core, memory, s = legacy
    memory.keep_english(s, "Time Code", {"mã thời gian": "{term}"}, apply=True)
    memory.keep_english(s, "Preset", {"cài đặt trước": "cài đặt {term}", "đặt trước": "{term}"}, apply=True)
    assert core.apply_rules(s, "Hiển thị mã thời gian.", "Displays the timecode.")["text"] == "Hiển thị timecode."
    assert core.apply_rules(s, "Tên đặt trước", "Preset Name")["text"] == "Tên Preset"
    assert core.search_tm(s, "Shoots with preset settings.")[0]["vi"] == "Chụp với cài đặt preset."


def test_feedback_learns_width_only_shortening(env):
    core, memory, s = env
    over = {"max_w": 150, "font_w": 24, "font_h": 38, "rows": 1, "linefeed": "Off"}
    roomy = {"max_w": 600, "font_w": 24, "font_h": 38, "rows": 1, "linefeed": "Off"}
    memory.record_feedback(s, "Anti-flicker Shoot Sel.", "Chọn chụp chống nhấp nháy", "Chống nhấp nháy", always=True, layout=over)
    assert core.apply_rules(s, "Chọn chụp chống nhấp nháy", "Anti-flicker Shoot Selection", roomy)["text"] == "Chọn chụp chống nhấp nháy"
    assert core.apply_rules(s, "Chọn chụp chống nhấp nháy", "Anti-flicker Shoot Selection", over)["text"] == "Chống nhấp nháy"


def test_feedback_keep_english_candidate(env):
    _, memory, s = env
    r = memory.record_feedback(s, "Range of Zoom Assist", "Dải hỗ trợ thu phóng", "Dải hỗ trợ Zoom")
    assert any(c.get("term") == "Zoom" for c in r.get("keep_english_candidates", []))


def test_suggest_short(env):
    core, _, s = env
    over = {"max_w": 150, "font_w": 24, "font_h": 38, "rows": 1, "linefeed": "Off"}
    cands = core.suggest_short(s, "Anti-flicker Shoot Sel.", "Chọn chụp chống nhấp nháy", over, limit=5)
    assert any(c["text"] == "Chống nhấp nháy" for c in cands)


def test_remember_translation_keeps_each_icon(env, tmp_path):
    core, memory, _ = env
    _seed_tm(tmp_path, [("<cE662>Focus Area", "<cE662>Vùng nét"), ("<cE6B1>Focus Area", "<cE6B1>Vùng nét"),
                        ("<cE628>Zoom<cE62B>", "<cE628>Zoom<cE62B>")])
    s = core.Store()
    r = memory.remember_translation(s, "<cE662>Focus Area", "<cE662>Vùng lấy nét")
    vis = {e["en"]: e["vi"] for e in s.tm}
    assert vis["<cE662>Focus Area"] == "<cE662>Vùng lấy nét" and vis["<cE6B1>Focus Area"] == "<cE6B1>Vùng lấy nét"
    r = memory.remember_translation(s, "<cE62A>Zoom", "<cE62A>Zoom")
    assert {e["en"]: e["vi"] for e in s.tm}["<cE628>Zoom<cE62B>"] == "<cE628>Zoom<cE62B>"
    memory.remember_translation(s, "<cE6B1>Focus Area", "<cE6B1>Vùng LN", tm_id="T1")
    vis = {e["en"]: e["vi"] for e in s.tm}
    assert vis["<cE6B1>Focus Area"] == "<cE6B1>Vùng LN" and vis["<cE662>Focus Area"] == "<cE662>Vùng lấy nét"
