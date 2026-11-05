"""Vercel entrypoint (every path is rewritten here by vercel.json): the public read-only alphaskill API (src/sony_alpha_viet/api.py) over `data-sample/`."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SONY_VN_DATA", str(ROOT / "data-sample"))  # filtered public sample, output of scripts/export_public_data.py

from sony_alpha_viet import api, server  # noqa: E402

server.make_public()
app = api.build_app()
