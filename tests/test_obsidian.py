"""Obsidian export/import/audit against a temp vault and the sample data."""
import json

import pytest


@pytest.fixture()
def vault(env, tmp_path, monkeypatch):
    core, memory, _ = env
    v = tmp_path / "vault"
    monkeypatch.setenv("SONY_VN_VAULT", str(v))
    import importlib
    import sony_alpha_viet.obsidian as obs
    importlib.reload(obs)
    with open(tmp_path / "data" / "tm.jsonl", "a", encoding="utf-8") as f:
        for i, (en, vi) in enumerate([("Aperture", "Khẩu độ"), ("Completed.", "Đã hoàn thành."), ("<cE662>Completed.", "<cE662>Đã hoàn tất."), ("<cE6B1>Aperture", "<cE6B1>Khẩu độ")]):
            f.write(json.dumps({"id": f"S{i}", "en": en, "vi": vi}, ensure_ascii=False) + "\n")
    return core, memory, core.Store(), obs, v / "AI Skills" / "Sony Alpha Việt"


def test_export_writes_expected_notes(vault):
    core, _, s, obs, root = vault
    out = obs.export(s)
    assert out["term_notes_written"] > 10 and out["consistency_groups"] == 1
    for name in ("Sony Alpha Việt.md", "Bảng thuật ngữ.md", "Giữ tiếng Anh.md", "Rà soát nhất quán.md", "Nhật ký học.md",
                 "Skill/SKILL.md", "Skill/references/glossary-vi.md", "Mẫu/Bài blog SEO.md"):
        assert (root / name).exists(), name
    props, body = obs.read_note(root / "Thuật ngữ" / "Aperture.md")
    assert props["vi"] == "khẩu độ" and props["locked"] is True and "S0" in body
    assert "Đã hoàn thành." in (root / "Rà soát nhất quán.md").read_text(encoding="utf-8")
    assert (root / "Thuật ngữ" / "Zoom.md").exists()  # keep_english terms get notes too


def test_edit_in_obsidian_then_import(vault):
    core, _, s, obs, root = vault
    obs.export(s)
    note = root / "Thuật ngữ" / "Aperture.md"
    obs.upsert_props(note, {"vi": "độ mở"})
    obs.write_note(root / "Thuật ngữ" / "New Thing.md", {"en": "New Thing", "vi": "điều mới"}, "tạo trong Obsidian")
    assert obs.export(s)["skipped_pending_edits"] == ["Aperture"]  # user edit is not overwritten
    plan = obs.import_terms(s)
    assert {c["en"] for c in plan["changes"]} == {"Aperture", "New Thing"}
    assert s.gl_by_en["aperture"]["vi"] == "khẩu độ"  # preview only
    obs.import_terms(s, apply=True)
    s2 = core.Store()
    assert s2.gl_by_en["aperture"]["vi"] == "độ mở" and s2.gl_by_en["new thing"]["locked"]
    assert obs.import_terms(s2)["changes"] == []


def test_audit_note_writes_report_and_props(vault):
    core, _, s, obs, root = vault
    from pathlib import Path
    src = Path(obs.SKILL / "examples" / "example-blog-post.md").read_text(encoding="utf-8")
    draft = root / "Blog" / "a7iv-vs-a7rv.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(src, encoding="utf-8")
    r = obs.audit_note("Blog/a7iv-vs-a7rv")
    props, body = obs.read_note(draft)
    assert props["seo_score"] == r["score"] and props["seo_complete"] is False and props["meta_title"].startswith("Sony A7 IV")
    assert "## Câu hỏi thường gặp" in body
    rep = (root / "Blog" / "a7iv-vs-a7rv — SEO audit.md").read_text(encoding="utf-8")
    assert "[[a7iv-vs-a7rv]]" in rep and "| 15* |" in rep
    assert obs.audit_note("Blog/a7iv-vs-a7rv")["score"] == r["score"]  # property rewrite doesn't change the audit
