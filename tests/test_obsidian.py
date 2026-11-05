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
    monkeypatch.setattr(obs.paths, "CONFIG", tmp_path / "config.json")  # never read the user's real config
    with open(tmp_path / "data" / "tm.jsonl", "a", encoding="utf-8") as f:
        for i, (en, vi) in enumerate([("Aperture", "Khẩu độ"), ("Completed.", "Đã hoàn thành."), ("<cE662>Completed.", "<cE662>Đã hoàn tất."), ("<cE6B1>Aperture", "<cE6B1>Khẩu độ")]):
            f.write(json.dumps({"id": f"S{i}", "en": en, "vi": vi}, ensure_ascii=False) + "\n")
    return core, memory, core.Store(), obs, v / "AI Skills" / "Sony Alpha Việt"


def test_export_writes_expected_notes(vault):
    core, _, s, obs, root = vault
    out = obs.export(s)
    assert out["term_notes_written"] > 10 and out["consistency_groups"] == 1
    for name in ("Sony Alpha Việt.md", "3 Thuật ngữ/Bảng thuật ngữ.md", "3 Thuật ngữ/Giữ tiếng Anh.md", "4 Dịch menu/Rà soát nhất quán.md",
                 "4 Dịch menu/Nhật ký học.md", "9 Skill/SKILL.md", "9 Skill/references/glossary-vi.md", "6 Blog/Mẫu/Bài blog SEO.md",
                 "1 Kiến thức/Kiến thức.md", "2 Giáo án/Giáo án.md", "1 Kiến thức/Phơi sáng/Khẩu độ.md"):
        assert (root / name).exists(), name
    props, body = obs.read_note(root / "3 Thuật ngữ" / "Aperture.md")
    assert props["vi"] == "khẩu độ" and props["locked"] is True and "S0" in body
    assert "Đã hoàn thành." in (root / "4 Dịch menu" / "Rà soát nhất quán.md").read_text(encoding="utf-8")
    assert (root / "3 Thuật ngữ" / "Zoom.md").exists()  # keep_english terms get notes too


def test_edit_in_obsidian_then_import(vault):
    core, _, s, obs, root = vault
    obs.export(s)
    note = root / "3 Thuật ngữ" / "Aperture.md"
    obs.upsert_props(note, {"vi": "độ mở"})
    obs.write_note(root / "3 Thuật ngữ" / "New Thing.md", {"en": "New Thing", "vi": "điều mới"}, "tạo trong Obsidian")
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
    draft = root / "6 Blog" / "a7iv-vs-a7rv.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(src, encoding="utf-8")
    r = obs.audit_note("6 Blog/a7iv-vs-a7rv")
    props, body = obs.read_note(draft)
    assert props["seo_score"] == r["score"] and props["seo_complete"] is False and props["meta_title"].startswith("Sony A7 IV")
    assert "## Câu hỏi thường gặp" in body
    rep = (root / "6 Blog" / "a7iv-vs-a7rv — SEO audit.md").read_text(encoding="utf-8")
    assert "[[a7iv-vs-a7rv]]" in rep and "| 15* |" in rep
    assert obs.audit_note("6 Blog/a7iv-vs-a7rv")["score"] == r["score"]  # property rewrite doesn't change the audit


def test_migrate_old_flat_layout(vault):
    core, _, s, obs, root = vault
    obs.write_note(root / "Thuật ngữ" / "Aperture.md", {"en": "Aperture", "vi": "độ mở"}, "sửa dở")
    obs.write_note(root / "Blog" / "nhap.md", {"title": "Nháp"}, "bản nháp")
    (root / "Bảng thuật ngữ.md").write_text("cũ", encoding="utf-8")
    out = obs.export(s)
    assert len(out["migrated"]["moved"]) == 3 and not (root / "Thuật ngữ").exists() and not (root / "Blog").exists()
    assert (root / "6 Blog" / "nhap.md").read_text(encoding="utf-8").endswith("bản nháp\n")
    assert out["skipped_pending_edits"] == ["Aperture"]  # the moved, still-unimported edit is kept
    assert obs.migrate(root) == {"moved": [], "conflicts": []}  # idempotent


def test_knowledge_mirror_edit_and_new_note(vault):
    core, _, s, obs, root = vault
    from sony_alpha_viet import knowledge
    out = obs.export(s)["knowledge"]
    assert out["notes"] == len(knowledge.load()) and out["pending_edits"] == []
    note = root / "1 Kiến thức" / "Phơi sáng" / "Khẩu độ.md"
    assert "kb_hash" in obs.read_note(note)[0] and obs.export(s)["knowledge"]["pending_edits"] == []  # re-export is clean
    note.write_text(note.read_text(encoding="utf-8") + "\nGhi chú của trainer.\n", encoding="utf-8")
    obs.write_note(root / "2 Giáo án" / "Buổi mới.md", {"title": "Buổi mới"}, "# Buổi mới\n\nTạo trong Obsidian.")
    assert obs.export(s)["knowledge"]["pending_edits"] == ["1 Kiến thức/Phơi sáng/Khẩu độ.md"]  # edit not overwritten
    plan = obs.import_knowledge()
    assert {(c["path"], c["kind"]) for c in plan["changes"]} == {("1 Kiến thức/Phơi sáng/Khẩu độ.md", "edited"), ("2 Giáo án/Buổi mới.md", "new")}
    obs.import_all(s, apply=True)
    assert "Ghi chú của trainer." in knowledge.get("Khẩu độ")["text"] and "kb_hash" not in knowledge.get("Khẩu độ")["text"]
    assert knowledge.get("Buổi mới")["path"] == "2 Giáo án/Buổi mới.md"
    assert obs.import_knowledge()["changes"] == []


def test_knowledge_folder_setting(vault, tmp_path):
    core, _, s, obs, root = vault
    (tmp_path / "config.json").write_text('{"vault_folder": "AI Skills/Sony Alpha Việt", "knowledge_folder": "Camera Wiki"}', encoding="utf-8")
    out = obs.export(s)
    wiki = tmp_path / "vault" / "Camera Wiki"
    assert out["knowledge"]["dir"] == str(wiki) and (wiki / "1 Kiến thức" / "Phơi sáng" / "Khẩu độ.md").exists()
    assert not (root / "1 Kiến thức").exists() and "[[Kiến thức\\|1 Kiến thức]]" in (root / "Sony Alpha Việt.md").read_text(encoding="utf-8")
