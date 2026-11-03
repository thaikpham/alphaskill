"""Vercel entrypoint: the public read-only alphaskill API (src/sony_alpha_viet/api.py) over `data/`."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SONY_VN_DATA", str(ROOT / "data"))  # git submodule: github.com/thaikpham/alphaskill-data

from sony_alpha_viet import api, server  # noqa: E402

server.make_public()
app = api.build_app()
