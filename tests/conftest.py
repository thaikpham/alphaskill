import json
import shutil
import pytest


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Setup test environment with data-sample copied to tmp."""
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / "data-sample"
    d = tmp_path / "data"
    shutil.copytree(src, d)
    monkeypatch.setenv("SONY_VN_DATA", str(d))
    import importlib
    import sony_alpha_viet.paths as paths
    import sony_alpha_viet.core as core
    import sony_alpha_viet.memory as memory
    importlib.reload(paths)
    importlib.reload(core)
    importlib.reload(memory)
    return core, memory, core.Store()


@pytest.fixture()
def data_with_glossary(env, tmp_path):
    """Setup with sample glossary entries for testing."""
    core, memory, s = env
    # Seed some glossary entries
    glossary_file = tmp_path / "data" / "glossary.json"
    glossary = [
        {"en": "Aperture", "vi": "khẩu độ", "short": "", "locked": False, "note": ""},
        {"en": "Exposure Comp.", "vi": "bù sáng", "short": "Bù", "locked": False, "note": ""},
        {"en": "Zoom", "vi": "thu phóng", "short": "", "locked": False, "note": ""},
    ]
    glossary_file.write_text(json.dumps(glossary, ensure_ascii=False, indent=1), encoding="utf-8")
    s.reload()
    return core, memory, s
