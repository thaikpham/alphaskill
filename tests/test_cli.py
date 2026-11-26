"""`alphaskill` dispatches to the existing entry points (src/sony_alpha_viet/cli.py)."""
import json
from pathlib import Path

from sony_alpha_viet import cli, paths

ROOT = Path(__file__).resolve().parents[1]


def test_entry_point_declared():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")  # no tomllib on Python 3.10
    assert 'alphaskill = "sony_alpha_viet.cli:main"' in text
    assert 'sony-alpha-viet-mcp = "sony_alpha_viet.server:main"' in text  # plugin, Gemini, Dockerfile still use it


def test_help_lists_every_command(capsys):
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    for name in cli.COMMANDS:
        assert f"\n  {name}" in out
    assert max(len(line) for line in out.splitlines()) <= 120


def test_unknown_command(capsys):
    assert cli.main(["nope"]) == 2
    assert "không có lệnh 'nope'" in capsys.readouterr().err


def test_subcommand_help_uses_alphaskill_prog(capsys):
    for cmd in ("serve", "agent", "obsidian"):
        try:
            cli.main([cmd, "--help"])
        except SystemExit as e:
            assert e.code == 0
        assert f"usage: alphaskill {cmd}" in capsys.readouterr().out


def test_review_pairs_usage(capsys):
    assert cli.main(["review-pairs"]) == 2
    assert "alphaskill review-pairs" in capsys.readouterr().out


def test_export_needs_private_data(monkeypatch, capsys):
    monkeypatch.setattr(paths, "DATA_SOURCE", "mặc định (dữ liệu mẫu)")
    assert cli.main(["export"]) == 2
    assert "SONY_VN_DATA" in capsys.readouterr().err


def test_publish_needs_private_data(monkeypatch, capsys):
    monkeypatch.delenv("SONY_VN_DATA", raising=False)
    monkeypatch.setattr(paths, "DATA_SOURCE", "mặc định (dữ liệu mẫu)")
    assert cli.main(["publish", "--no-push"]) == 2
    assert "SONY_VN_DATA" in capsys.readouterr().err


def test_export_explicit_paths(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "glossary.json").write_text(json.dumps([{"en": "Zoom", "vi": "Zoom", "note": "S12345"}]), encoding="utf-8")
    (src / "rules.json").write_text('{"substitutions": [], "exact": {}, "banned": []}', encoding="utf-8")
    (src / "tm.jsonl").write_text('{"en": "a", "vi": "b"}\n', encoding="utf-8")
    assert cli.main(["export", str(src), str(out)]) == 0
    assert (out / "tm.jsonl").read_text(encoding="utf-8") == ""
    assert "note" not in json.loads((out / "glossary.json").read_text(encoding="utf-8"))[0]


def test_build_check_passes():
    assert cli.main(["build", "--check"]) == 0
