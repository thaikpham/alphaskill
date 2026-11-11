"""Sony doc corpus: VNI decoding, docx links, phrase search, glossary-vs-Sony report, vault export (synthetic corpus)."""
import json
import urllib.error
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
    d.mkdir(parents=True, exist_ok=True)
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


def test_ingest_helpguide(tmp_path, monkeypatch):
    """Fake helpguide ingest: extract all contents links, fetch each, extract <main>."""
    from sony_alpha_viet import docs

    # Create fake HTML pages - links can be anywhere in index HTML (not just <main>)
    index_html = """<html><title>ILCE-7RM5 | Help Guide | Topics</title>
    <body>
    <a href="contents/01-basics.html">Getting Started</a>
    <div><a href="contents/02-focus.html">Focus Area Settings</a></div>
    </body></html>"""

    page1 = """<html><body><main><h1>Getting Started</h1>
    <p>Turn on the camera using the power switch.</p>
    <p>Press the shutter button halfway to focus.</p>
    </main></body></html>"""

    page2 = """<html><body><main><h1>Focus Area Settings</h1>
    <p>Use [Menu] &gt; [Focus Area] to set focus mode.</p>
    <p>Options include <b>Wide</b>, <b>Zone</b>, and <b>Spot</b>.</p>
    </main></body></html>"""

    def mock_fetch(url, timeout=5):
        if "index.html" in url:
            return index_html
        elif "01-basics" in url:
            return page1
        elif "02-focus" in url:
            return page2
        raise urllib.error.URLError("not found")

    monkeypatch.setattr("sony_alpha_viet.docs._fetch_url", mock_fetch)

    data_dir = tmp_path / "data"
    result = docs.ingest_helpguide(
        "https://helpguide.sony.net/ilc/2230/v1/en/index.html",
        data=data_dir
    )

    assert result["ok"]
    assert result["model"] == "ILCE-7RM5"
    assert result["pages"] == 2
    assert result["doc_id"] == "helpguide-ilce-7rm5-en"

    # Check markdown file was created
    md_file = data_dir / "docs" / "helpguide-ilce-7rm5-en.md"
    assert md_file.exists()
    content = md_file.read_text(encoding="utf-8")
    assert "## Trang 1" in content
    assert "## Trang 2" in content
    assert "Getting Started" in content
    assert "Focus Area" in content
    assert "[Menu]" in content  # [Menu] brackets preserved

    # Check index.json
    import json
    index_data = json.loads((data_dir / "docs" / "index.json").read_text(encoding="utf-8"))
    doc_entry = next((d for d in index_data["docs"] if d["id"] == "helpguide-ilce-7rm5-en"), None)
    assert doc_entry is not None
    assert doc_entry["lang"] == "en"
    assert doc_entry["kind"] == "Help Guide (EN)"
    assert "source_url" in doc_entry


def test_search_includes_lang(tmp_path):
    """search() results include lang field."""
    from sony_alpha_viet import docs

    _corpus(tmp_path / "data")

    # Add a fake EN doc entry manually
    import json
    index_file = tmp_path / "data" / "docs" / "index.json"
    idx = json.loads(index_file.read_text(encoding="utf-8"))
    idx["docs"].append({
        "id": "fake-en", "model": "ILCE-7RM5", "kind": "Help Guide (EN)",
        "lang": "en", "pages": 1, "chars": 100, "source_url": "https://example.com"
    })
    index_file.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")

    # Create markdown for the EN doc
    (tmp_path / "data" / "docs" / "fake-en.md").write_text("## Trang 1\n\nFocus Area controls shutter speed.", encoding="utf-8")

    hits = docs.search("lấy nét", data=tmp_path / "data")
    # Should find Vietnamese docs (lang=vi)
    assert any(h["lang"] == "vi" for h in hits)

    hits_en = docs.search("Focus Area", data=tmp_path / "data")
    # Should find EN doc
    assert any(h["lang"] == "en" for h in hits_en)


def test_term_report_skips_en_docs(env, tmp_path):
    """term_report only checks Vietnamese docs."""
    from sony_alpha_viet import docs
    core, _, s = env

    _corpus(tmp_path / "data")

    # Add a fake EN doc entry
    import json
    index_file = tmp_path / "data" / "docs" / "index.json"
    idx = json.loads(index_file.read_text(encoding="utf-8"))
    idx["docs"].append({
        "id": "fake-en", "model": "ILCE-7RM5", "kind": "Help Guide (EN)",
        "lang": "en", "pages": 1, "chars": 200, "source_url": "https://example.com"
    })
    index_file.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")

    # Create markdown with banned term
    (tmp_path / "data" / "docs" / "fake-en.md").write_text(
        "## Trang 1\n\nShutter button and aperture controls. Playback button.", encoding="utf-8"
    )

    r = docs.term_report(s, tmp_path / "data")
    # Report should only have 2 docs (the VN ones), not 3
    assert r["docs"] == 2
    # Should not find "button" as a banned form since EN doc is skipped
    banned_uses = [b["sony_uses"] for b in r["banned_forms_sony_uses"]]
    assert "button" not in banned_uses  # EN text should not be analyzed


def test_ingest_helpguide_merges_with_pdf_ingest(tmp_path, monkeypatch):
    """Re-running PDF ingest should preserve helpguide entries."""
    from sony_alpha_viet import docs
    import json

    # First, add a fake helpguide entry
    data_dir = tmp_path / "data"
    docs_dir = data_dir / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "helpguide-test.md").write_text("## Trang 1\n\nTest content.", encoding="utf-8")

    idx_data = {
        "source": "https://helpguide.sony.net/",
        "docs": [{
            "id": "helpguide-test", "model": "TEST", "kind": "Help Guide (EN)",
            "lang": "en", "pages": 1, "chars": 50, "source_url": "https://helpguide.sony.net/test"
        }],
        "links": [], "duplicates": []
    }
    (docs_dir / "index.json").write_text(json.dumps(idx_data, ensure_ascii=False), encoding="utf-8")

    # Mock PDF ingest - create a fake PDF environment
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf_file = pdf_dir / "test.pdf"
    pdf_file.write_text("test", encoding="utf-8")  # fake PDF

    # Mock _pdf_pages to avoid needing pdftotext
    def mock_pdf_pages(path):
        return ["Test PDF content"]

    monkeypatch.setattr("sony_alpha_viet.docs._pdf_pages", mock_pdf_pages)

    # Run ingest - should preserve the helpguide entry
    docs.ingest(str(pdf_dir), data=data_dir)

    # Check that helpguide entry is still there
    final_idx = json.loads((docs_dir / "index.json").read_text(encoding="utf-8"))
    helpguide_entries = [d for d in final_idx["docs"] if "source_url" in d]
    assert len(helpguide_entries) >= 1
    assert any(d["id"] == "helpguide-test" for d in helpguide_entries)
