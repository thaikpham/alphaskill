"""Data directory resolution for sony-alpha-viet: reads SONY_VN_DATA env, falls back to XDG_DATA_HOME."""
import json
import os
import subprocess
from pathlib import Path

# Data directory, first match wins:
#   1. $SONY_VN_DATA
#   2. "data" in $XDG_CONFIG_HOME/sony-alpha-viet/config.json (~/.config/…) — works in shells that don't load ~/.bashrc
#   3. $XDG_DATA_HOME/sony-alpha-viet/data (~/.local/share/…), created from data-sample on first use
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "sony-alpha-viet" / "config.json"


def _resolve() -> tuple[Path, str]:
    if os.environ.get("SONY_VN_DATA"):
        return Path(os.environ["SONY_VN_DATA"]).expanduser(), "env SONY_VN_DATA"
    if CONFIG.exists():
        try:
            d = json.loads(CONFIG.read_text(encoding="utf-8")).get("data")
            if d:
                return Path(d).expanduser(), f"config {CONFIG}"
        except (OSError, ValueError):
            pass
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "sony-alpha-viet" / "data", "mặc định (dữ liệu mẫu)"


DATA, DATA_SOURCE = _resolve()

# Ensure data directory exists on first use; init git repo if missing
def ensure_data_dir():
    """Create DATA dir if missing, copy data-sample, and git init."""
    if DATA.exists():
        return
    DATA.mkdir(parents=True, exist_ok=True)

    # Copy data-sample/ from package
    sample_dir = Path(__file__).resolve().parent.parent.parent / "data-sample"
    if sample_dir.exists():
        import shutil
        for item in sample_dir.iterdir():
            if item.is_file():
                (DATA / item.name).write_bytes(item.read_bytes())
            elif item.is_dir():
                shutil.copytree(item, DATA / item.name, dirs_exist_ok=True)

    # git init in DATA dir (ignore failure if git missing)
    try:
        subprocess.run(["git", "init"], cwd=DATA, capture_output=True, check=False)
    except FileNotFoundError:
        pass
