"""Tests for core engine (adapted from sony-vn-translator)."""
import json
import pytest


def test_fit(env):
    """Test OSD width estimation."""
    core, _, _ = env
    assert core.fit("Bù sáng", 280, 29, 38)["verdict"] == "OK"
    assert core.fit("Kết nối điện thoại thông minh mới rất dài", 200, 26, 34)["verdict"] == "OVER"


def test_audit_flags(data_with_glossary):
    """Test audit issue detection."""
    core, _, s = data_with_glossary
    # English residue check (no glossary entry, no keep_english)
    a = core.audit(s, "Fan Speed", "Tốc độ fan")
    assert any(i["type"] == "english_residue" for i in a["issues"]), "Should flag 'fan' as english residue"


def test_lookup_terms(data_with_glossary):
    """Test glossary lookup."""
    core, _, s = data_with_glossary
    results = core.lookup_terms(s, "Aperture")
    assert results, "Should find Aperture"
    assert results[0]["en"] == "Aperture"


def test_search_tm_empty(env):
    """Test TM search with empty sample data."""
    core, _, s = env
    # data-sample has empty tm.jsonl
    hits = core.search_tm(s, "Aperture")
    # Should return empty or default
    assert isinstance(hits, list)


def test_memory_record_term(data_with_glossary):
    """Test recording a user term decision."""
    core, memory, s = data_with_glossary
    memory.record_term(s, "Bracket Mode", "chế độ bù sáng liên tục", note="test")
    s.reload()
    # Check if it was added to glossary
    assert any(g["en"] == "Bracket Mode" for g in s.glossary)


def test_suggest_short_basic(data_with_glossary):
    """Test shortening suggestions."""
    core, _, s = data_with_glossary
    layout = {"max_w": 150, "font_w": 24, "font_h": 38, "rows": 1, "linefeed": "Off"}
    candidates = core.suggest_short(
        s,
        en="Anti-flicker Shoot Sel.",
        vi="Chọn chụp chống nhấp nháy",
        layout=layout,
        limit=5
    )
    # Should return a list of candidates
    assert isinstance(candidates, list)
