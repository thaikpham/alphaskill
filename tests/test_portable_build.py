"""Portable bundle: llms-full.txt, llms-blog.txt, llms-knowledge.txt and llms.txt stay in sync with their sources (scripts/build_portable.py)."""
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
RAW_PREFIX = "https://raw.githubusercontent.com/thaikpham/alphaskill/main/"
RAW_URL = re.compile(r"https://raw\.githubusercontent\.com/thaikpham/alphaskill/main/([^)\s]+)")
BUNDLES = ["llms-full.txt", "llms-blog.txt", "llms-knowledge.txt"]
CORE_BUDGET = 95 * 1024  # build target is 90 KB; the test allows 95 KB


def _load_build():
    spec = importlib.util.spec_from_file_location("build_portable", ROOT / "scripts" / "build_portable.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load_build()


def test_generated_files_match_sources():
    stale = [p.relative_to(ROOT).as_posix() for p, text in build.build().items()
             if not p.is_file() or p.read_bytes() != text.encode("utf-8")]
    assert stale == []


def test_root_bundles_exist_and_are_current():
    root_files = {p.name: text for p, text in build.build().items() if p.parent == ROOT}
    for name in [*BUNDLES, "llms.txt"]:
        path = ROOT / name
        assert path.is_file(), name
        assert path.read_bytes() == root_files[name].encode("utf-8"), name


def test_llms_full_lists_every_glossary_term():
    full = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    glossary = json.loads((ROOT / "data-sample" / "glossary.json").read_text(encoding="utf-8"))
    assert f"Bảng thuật ngữ: {len(glossary)} mục" in full
    missing = [e["en"] for e in glossary if build.cell(e["en"]) not in full]
    assert missing == []


def test_llms_full_within_core_budget():
    assert (ROOT / "llms-full.txt").stat().st_size <= CORE_BUDGET


def test_llms_full_contains_system_prompt():
    full = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    prompt = (ROOT / "portable" / "system-prompt.md").read_text(encoding="utf-8")
    assert build.demote(prompt, 2).strip() in full


def test_llms_txt_links_each_bundle():
    index = (ROOT / "llms.txt").read_text(encoding="utf-8")
    missing = [name for name in BUNDLES if f"{RAW_PREFIX}{name}" not in index]
    assert missing == []


def test_llms_txt_raw_links_point_to_existing_files():
    paths = RAW_URL.findall((ROOT / "llms.txt").read_text(encoding="utf-8"))
    assert paths
    missing = [p for p in map(unquote, paths) if not (ROOT / p).is_file()]
    assert missing == []


def test_llms_full_glossary_applies_replacement_rules():
    full = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    row = next(line for line in full.split("\n") if line.startswith("| Zebra Display |"))
    assert "sọc vằn" in row
    assert "hiển thị Zebra" not in row
    assert "(đã áp quy tắc r115)" in row


def test_glossary_vi_is_fixed_point_of_rules():
    from sony_alpha_viet import core
    store = build.rules_store()
    glossary = json.loads((ROOT / "data-sample" / "glossary.json").read_text(encoding="utf-8"))
    rendered, _ = build.rule_glossary(glossary)
    table = (ROOT / "portable" / "knowledge" / "glossary-full.md").read_text(encoding="utf-8")
    for e in rendered:
        assert f"| {build.cell(e['en'])} | {build.cell(e['vi'])} |" in table, e["en"]
        for field in ("vi", "short"):
            value = e.get(field) or ""
            if value:
                assert core.apply_rules(store, value, e["en"])["text"] == value, (e["en"], field)


def test_exception_rule_refers_to_section_title():
    full = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    assert "quy tắc mục" not in full
    assert 'quy tắc "GIÁ TRỊ KỸ THUẬT ĐƯỢC GIỮ NGUYÊN (CÓ NHÃN CHUẨN)"' in full


def test_llms_bundles_have_no_short_line_runs():
    runs = []
    for path in sorted(ROOT.glob("llms*.txt")):
        streak = 0
        for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            streak = streak + 1 if len(line.strip()) <= 2 else 0
            if streak == 10:
                runs.append(f"{path.name}:{number}")
    assert runs == []
