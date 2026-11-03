"""Sony doc corpus: VNI decoding, docx links, phrase search, glossary-vs-Sony report, vault export (synthetic corpus)."""
import json
import zipfile


def test_vni_to_unicode():
    from sony_alpha_viet.docs import looks_vni, vni_to_unicode
    s = "Ñaûm baûo pin quay vaøo ñuùng höôùng, vaø gaén pin trong khi nhaán caàn khoùa pin. Löu yù khi chuïp lieân tieáp. " * 2
    assert looks_vni(s)
    out = vni_to_unicode("Ñaûm baûo pin quay vaøo ñuùng höôùng. Ñaëc bieät chuù yù, chæ daønh cho laàn ñaàu tieân. Thaân maùy.")
    assert out == "Đảm bảo pin quay vào đúng hướng. Đặc biệt chú ý, chỉ dành cho lần đầu tiên. Thân máy."
    assert not looks_vni("Đảm bảo pin quay vào đúng hướng. Máy ảnh kỹ thuật số ống kính rời. " * 5)


def test_docx_links(tmp_path):
    from sony_alpha_viet.docs import _docx_links
    p = tmp_path / "Menu.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship Id="rId5" Type="x" Target="https://helpguide.sony.net/a.html" TargetMode="External"/></Relationships>')
        z.writestr("word/document.xml", '<w:document><w:hyperlink r:id="rId5"><w:r><w:t>ZV-E10 | Help Guide</w:t></w:r></w:hyperlink></w:document>')
    assert _docx_links(p) == [{"title": "ZV-E10 | Help Guide", "url": "https://helpguide.sony.net/a.html"}]


def _corpus(data):
    d = data / "docs"
    d.mkdir()
    texts = {"old": "## Trang 1\n\nNhấn nút màn trập nửa chừng để lấy nét.\nNhấn nút (phát lại).",
             "new": "## Trang 1\n\nNhấn nút chụp nửa chừng để lấy\nnét. Ghép đôi (Kết nối Smartphone) với điện thoại.\n\n## Trang 2\n\nNút chụp và khẩu độ."}
    for k, v in texts.items():
        (d / f"{k}.md").write_text(v, encoding="utf-8")
    (d / "index.json").write_text(json.dumps({"docs": [
        {"id": "old", "file": "A6400.pdf", "model": "ILCE-6400", "code": "D-1", "kind": "Hướng dẫn khởi động", "pages": 1, "encoding": "vni"},
        {"id": "new", "file": "A7 M5.pdf", "model": "ILCE-7M5", "code": "5-1", "kind": "Hướng dẫn khởi động", "pages": 2, "encoding": "unicode"}],
        "links": [{"title": "Help Guide", "url": "https://helpguide.sony.net/x"}], "duplicates": []}, ensure_ascii=False), encoding="utf-8")


def test_search_and_term_report(env, tmp_path):
    core, _, s = env
    from sony_alpha_viet import docs
    _corpus(tmp_path / "data")
    hits = docs.search("lấy nét", data=tmp_path / "data")
    assert {h["model"] for h in hits} == {"ILCE-6400", "ILCE-7M5"}  # phrase found across a line break too
    assert docs.search("nút chụp", 10, tmp_path / "data")[0]["page"] == 1 and len(docs.search("nút chụp", 10, tmp_path / "data")) == 2
    r = docs.term_report(s, tmp_path / "data")
    banned = {b["sony_uses"]: b["by_model"] for b in r["banned_forms_sony_uses"]}
    assert banned["nút màn trập"] == {"ILCE-6400": 1} and "phát lại" in banned
    assert any(x["vi"] == "nút chụp" for x in r["locked_terms_used_by_sony"])


def test_vault_export_includes_docs(env, tmp_path, monkeypatch):
    core, _, s = env
    _corpus(tmp_path / "data")
    monkeypatch.setenv("SONY_VN_VAULT", str(tmp_path / "vault"))
    import importlib
    import sony_alpha_viet.obsidian as obs
    importlib.reload(obs)
    monkeypatch.setattr(obs.paths, "CONFIG", tmp_path / "config.json")  # never read the user's real config
    assert obs.export(s)["sony_docs"] == 2
    root = tmp_path / "vault" / "AI Skills" / "Sony Alpha Việt" / "5 Tài liệu Sony"
    note = (root / "ILCE-7M5 — Hướng dẫn khởi động.md").read_text(encoding="utf-8")
    assert "model: ILCE-7M5" in note and "[[3 Thuật ngữ/Shutter Button|Shutter Button]]" in note
    report = (root / "Đối chiếu thuật ngữ với Sony.md").read_text(encoding="utf-8")
    assert "`nút màn trập`" in report and "ILCE-6400 (1)" in report
