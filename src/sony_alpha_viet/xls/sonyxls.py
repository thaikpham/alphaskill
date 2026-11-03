"""Read/write Sony *TranslationCheck_VN.xls review files (sheet VN). Writes only AN/AU/AV, byte-faithfully."""
from __future__ import annotations

import os

from . import biff

# 0-based column indexes in sheet "VN"
COL = {"sid": 1, "font_h": 5, "font_w": 6, "max_h": 9, "max_w": 10, "rows": 11, "linefeed": 16, "reference": 26,
       "en": 27, "en_full": 28, "vi": 29, "vi_full": 30, "an": 39, "au": 46, "av": 47}
AU_VALUES = ["Suggest a better translation", "By a fatal error as photographic terms", "By a spelling error",
             "By a grammatical error", "By the other reason"]


def read_rows(path: str) -> list[dict]:
    import xlrd
    sh = xlrd.open_workbook(path).sheet_by_name("VN")
    out = []
    for r in range(2, sh.nrows):
        sid = str(sh.cell_value(r, COL["sid"]))
        if not sid.startswith("S"):
            continue
        g = lambda k: sh.cell_value(r, COL[k]) if COL[k] < sh.ncols else ""
        def num(v, d):
            try:
                return int(float(v))
            except (TypeError, ValueError):
                return d
        out.append({"row": r + 1, "sid": sid, "en": str(g("en")), "vi": str(g("vi")), "an": str(g("an")), "au": str(g("au")), "av": str(g("av")),
                    "reference": str(g("reference"))[:400],
                    "layout": {"max_w": num(g("max_w"), 480), "font_w": num(g("font_w"), 27), "font_h": num(g("font_h"), 36),
                               "rows": num(g("rows"), 1), "linefeed": str(g("linefeed") or "Off")}})
    return out


def write_proposals(src: str, out: str, proposals: list[dict], overwrite: bool = False) -> dict:
    """proposals: [{row, sid, an, au, av}] (row is 1-based). Refuses on S# mismatch or AN without AU/AV.
    overwrite=True revises AN/AU/AV cells that already have a value (otherwise only blank cells are filled)."""
    import olefile
    import xlrd
    if os.path.abspath(src) == os.path.abspath(out):
        raise ValueError("out must differ from src (never overwrite the original)")
    sh = xlrd.open_workbook(src).sheet_by_name("VN")
    targets = {}
    for p in proposals:
        ri = int(p["row"]) - 1
        if sh.cell_value(ri, COL["sid"]) != p["sid"]:
            raise ValueError(f"row {p['row']}: S# is {sh.cell_value(ri, COL['sid'])}, not {p['sid']}")
        if p.get("an") and (not p.get("au") or not p.get("av")):
            raise ValueError(f"row {p['row']}: AN needs AU and AV")
        if p.get("au") and p["au"] not in AU_VALUES:
            raise ValueError(f"row {p['row']}: AU must be one of {AU_VALUES}")
        targets[(ri, COL["an"])] = p.get("an", "")
        targets[(ri, COL["au"])] = p.get("au", "")
        targets[(ri, COL["av"])] = p.get("av", "")
    raw = open(src, "rb").read()
    wb = olefile.OleFileIO(src).openstream("Workbook").read()
    new, st = biff.apply_cells(wb, targets, overwrite)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "wb").write(biff.ole_replace_stream(raw, "Workbook", new))
    # verify
    sh2 = xlrd.open_workbook(out).sheet_by_name("VN")
    bad = [k for k, v in targets.items() if sh2.cell_value(*k) != v]
    return {"written": len(proposals), "cells": st.get("cells"), "verify_mismatches": len(bad), "out": out}
