"""Tests for scripts/export_public_data.py"""
import tempfile
import sys
from pathlib import Path

import pytest

# Import export_public_data function
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.export_public_data import export_public_data


def test_export_knowledge_with_nested_folders():
    """Export knowledge preserves folder structure and files."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        out = Path(tmp) / "out"
        src.mkdir()
        (src / "knowledge").mkdir()

        # Create nested structure
        (src / "knowledge" / "folder1").mkdir()
        (src / "knowledge" / "folder1" / "subfolder").mkdir()
        (src / "knowledge" / "folder1" / "note1.md").write_text("# Note 1\nContent", encoding="utf-8")
        (src / "knowledge" / "folder1" / "subfolder" / "note2.md").write_text("# Note 2\nContent", encoding="utf-8")
        (src / "knowledge" / "folder2").mkdir()
        (src / "knowledge" / "folder2" / "note3.md").write_text("# Note 3\nContent", encoding="utf-8")

        # Minimal required files in src
        (src / "glossary.json").write_text("[]", encoding="utf-8")
        (src / "rules.json").write_text('{"substitutions": [], "exact": {}, "banned": []}', encoding="utf-8")

        export_public_data(src, out)

        # Check structure is preserved
        assert (out / "knowledge" / "folder1" / "note1.md").read_text(encoding="utf-8") == "# Note 1\nContent"
        assert (out / "knowledge" / "folder1" / "subfolder" / "note2.md").read_text(encoding="utf-8") == "# Note 2\nContent"
        assert (out / "knowledge" / "folder2" / "note3.md").read_text(encoding="utf-8") == "# Note 3\nContent"


def test_export_refuses_s_numbers():
    """Export raises and writes nothing to knowledge if any note contains S-number."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        out = Path(tmp) / "out"
        src.mkdir()
        (src / "knowledge").mkdir()

        # Create a note with S-number
        (src / "knowledge" / "note_with_snumber.md").write_text("# Note\nSee S12345 in docs", encoding="utf-8")

        # Minimal required files in src
        (src / "glossary.json").write_text("[]", encoding="utf-8")
        (src / "rules.json").write_text('{"substitutions": [], "exact": {}, "banned": []}', encoding="utf-8")

        with pytest.raises(ValueError, match="S-number found"):
            export_public_data(src, out)

        # Verify nothing was written to knowledge
        assert not (out / "knowledge").exists()


def test_export_tm_always_empty():
    """tm.jsonl is always empty even if source has data."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        out = Path(tmp) / "out"
        src.mkdir()
        (src / "glossary.json").write_text("[]", encoding="utf-8")
        (src / "rules.json").write_text('{"substitutions": [], "exact": {}, "banned": []}', encoding="utf-8")
        (src / "tm.jsonl").write_text('{"en": "hello", "vi": "xin chào"}', encoding="utf-8")

        export_public_data(src, out)

        assert (out / "tm.jsonl").read_text(encoding="utf-8") == ""


def test_export_knowledge_on_previous_export():
    """Exporting again deletes previous knowledge export."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        out = Path(tmp) / "out"
        src.mkdir()
        (src / "knowledge").mkdir()
        (src / "glossary.json").write_text("[]", encoding="utf-8")
        (src / "rules.json").write_text('{"substitutions": [], "exact": {}, "banned": []}', encoding="utf-8")

        # First export
        (src / "knowledge" / "old_note.md").write_text("# Old", encoding="utf-8")
        export_public_data(src, out)
        assert (out / "knowledge" / "old_note.md").exists()

        # Second export with different file
        (src / "knowledge" / "old_note.md").unlink()
        (src / "knowledge" / "new_note.md").write_text("# New", encoding="utf-8")
        export_public_data(src, out)

        # Old file should be gone, new file present
        assert not (out / "knowledge" / "old_note.md").exists()
        assert (out / "knowledge" / "new_note.md").exists()
