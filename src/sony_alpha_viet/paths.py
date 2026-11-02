"""Data directory resolution for sony-alpha-viet: reads SONY_VN_DATA env, falls back to XDG_DATA_HOME."""
import os
import subprocess
from pathlib import Path

# Data directory: $SONY_VN_DATA if set, else $XDG_DATA_HOME/sony-alpha-viet/data, else ~/.local/share/sony-alpha-viet/data
_env = os.environ.get("SONY_VN_DATA")
if _env:
    DATA = Path(_env)
else:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        DATA = Path(xdg_data_home) / "sony-alpha-viet" / "data"
    else:
        DATA = Path.home() / ".local" / "share" / "sony-alpha-viet" / "data"

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
