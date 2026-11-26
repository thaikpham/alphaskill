"""Apply an agreed-terms table (cross-check sheet: English | current Vietnamese | AGREED) to Sony *_VN.xls files.

Rules follow the 26/11/2026 SEV cross-check run on the ILDC files ①–⑧:
- Rows kept in English, rows with no match and rows whose AN already equals AGREED are left alone.
- AGREED equal to the present translation (VI) while an old AN exists: AN/AU/AV are cleared.
- New proposal: AN = AGREED, AU "Suggest a better translation" ("By a spelling error" for case or diacritics only),
  AV = concrete reason in English ('old' → 'new').
- Existing AN that differs: AN = AGREED, AU kept, AV = "<old AV> | Review 2: <reason>".
- AGREED estimated to overflow the frame: first re-broken (same words, new line breaks, see core.rebreak);
  if that fits, AN is the re-broken text and AV says so. Otherwise skipped and listed, or with apply_overflow=True written with AV starting
  "Width to be confirmed with SonyTool (estimated overflow)." (the user then checks those rows in SonyTool).
"""
from __future__ import annotations

import csv
import difflib
import re
import unicodedata
from pathlib import Path

from .. import core

SUGGEST = "Suggest a better translation"
SPELLING = "By a spelling error"
WIDTH_NOTE = "Width to be confirmed with SonyTool (estimated overflow). "
REBROKEN = "Line breaks re-arranged to fit the frame (wording as agreed). "
REWORDED = "Reworded for natural, concise Vietnamese UI text (agreed in SEV cross-check with Sony VN trainers)."
_TOK = re.compile(r"\w+|[^\w\s]")


def load_agreed(path: str | Path) -> dict[str, dict[str, str]]:
    """CSV/TSV with header columns English, Vietnamese (optional) and AGREED.
    Returns {english: {current_vietnamese: agreed}}; current_vietnamese is "" when the column is missing."""
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        rows = list(csv.DictReader(f, dialect=csv.Sniffer().sniff(sample, delimiters=",\t;")))
    if not rows:
        return {}
    keys = {k.strip().lower(): k for k in rows[0] if k}
    en_k, ag_k = keys.get("english"), keys.get("agreed")
    if not en_k or not ag_k:
        raise ValueError("agreed table needs columns 'English' and 'AGREED'")
    vi_k = keys.get("vietnamese")
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        en, ag = r.get(en_k) or "", r.get(ag_k) or ""
        if en and ag:
            out.setdefault(en, {}).setdefault((r.get(vi_k) or "") if vi_k else "", ag)
    return out


def _strip_marks(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def reason(old: str, new: str) -> str:
    """Short English reason: 'old' → 'new' for short strings, changed phrases (one word of context) otherwise."""
    if "\n" not in old + new and len(old) + len(new) <= 70:
        return f"'{old}' → '{new}'."
    sa = [m.span() for m in _TOK.finditer(old)]
    sb = [m.span() for m in _TOK.finditer(new)]
    ta, tb = [old[x:y] for x, y in sa], [new[x:y] for x, y in sb]
    ops = [o for o in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes() if o[0] != "equal"]
    if not ops:
        return "Spacing corrected." if old != new else ""
    blocks: list[list[int]] = []
    for _, i1, i2, j1, j2 in ops:
        i1, j1, i2, j2 = max(i1 - 1, 0), max(j1 - 1, 0), min(i2 + 1, len(ta)), min(j2 + 1, len(tb))
        if blocks and i1 <= blocks[-1][1]:
            blocks[-1] = [blocks[-1][0], max(i2, blocks[-1][1]), blocks[-1][2], max(j2, blocks[-1][3])]
        else:
            blocks.append([i1, i2, j1, j2])
    parts = []
    for i1, i2, j1, j2 in blocks:
        a = old[sa[i1][0]:sa[i2 - 1][1]] if i2 > i1 else ""
        b = new[sb[j1][0]:sb[j2 - 1][1]] if j2 > j1 else ""
        parts.append(f"'{a}' → '{b}'".replace("\n", " "))
    text = "; ".join(parts) + "."
    return text if len(text) <= 110 and len(parts) <= 3 else REWORDED


def fits(en: str, vi: str, layout: dict | None) -> bool:
    """Estimated width OK (not OVER) and no more lines than max(Rows, English lines) when Line Feed is Off."""
    if not layout or not layout.get("max_w"):
        return True
    lf = str(layout.get("linefeed") or "Off")
    f = core.fit(vi, layout["max_w"], layout.get("font_w", 27), layout.get("font_h", 36), layout.get("rows", 1), lf)
    if f.get("verdict") == "OVER":
        return False
    return lf.lower() == "on" or len(vi.split("\n")) <= max(int(layout.get("rows") or 1), len(en.split("\n")))


def rebreak(en: str, vi: str, layout: dict | None) -> str | None:
    """vi with new line breaks that fit the layout (allowed lines = max(Rows, English lines)), or None."""
    if not layout or not layout.get("max_w"):
        return None
    lay = core.effective_layout(en, {"max_w": layout["max_w"], "font_w": layout.get("font_w", 27),
                                     "font_h": layout.get("font_h", 36), "rows": layout.get("rows", 1),
                                     "linefeed": str(layout.get("linefeed") or "Off")})
    rb = core.rebreak(vi, **lay)
    return rb if rb and fits(en, rb, layout) else None


def plan(rows: list[dict], agreed: dict[str, dict[str, str]], apply_overflow: bool = False) -> dict:
    """rows: sonyxls.read_rows() output. Returns {proposals, skipped_width, stats}; proposals go to write_proposals(overwrite=True)."""
    proposals, skipped = [], []
    stats = {"rows": len(rows), "no_match": 0, "already": 0, "new": 0, "review2": 0, "cleared": 0,
             "width_flagged": 0, "width_skipped": 0, "rebroken": 0}
    for r in rows:
        en, vi, an = r["en"], r["vi"], r["an"]
        options = agreed.get(en)
        if not options:
            stats["no_match"] += 1
            continue
        eff = an or vi
        ag = options.get(eff) or options.get(vi) or options.get("") or next(iter(options.values()))
        if ag == eff:
            stats["already"] += 1
            continue
        base = {"row": r["row"], "sid": r["sid"]}
        if ag == vi:  # agreed is the present translation: the old proposal goes
            proposals.append({**base, "an": "", "au": "", "av": ""})
            stats["cleared"] += 1
            continue
        note = ""
        if not fits(en, ag, r.get("layout")):
            rb = rebreak(en, ag, r.get("layout"))
            if rb:  # same words, new line breaks: fits without rewording
                ag, note = rb, REBROKEN
                stats["rebroken"] += 1
        if not note and not fits(en, ag, r.get("layout")):
            if not apply_overflow:
                skipped.append({**base, "en": en, "current": eff, "agreed": ag, "layout": r.get("layout")})
                stats["width_skipped"] += 1
                continue
            note = WIDTH_NOTE
            stats["width_flagged"] += 1
        why = note + reason(eff, ag)
        if note == REBROKEN and why.endswith("Spacing corrected."):
            why = REBROKEN.strip()
        if an:
            av = (r["av"] + " | " if r["av"] else "") + "Review 2: " + why
            proposals.append({**base, "an": ag, "au": r["au"] or SUGGEST, "av": av})
            stats["review2"] += 1
        else:
            au = SPELLING if _strip_marks(vi) == _strip_marks(ag) else SUGGEST
            proposals.append({**base, "an": ag, "au": au, "av": why})
            stats["new"] += 1
    return {"proposals": proposals, "skipped_width": skipped, "stats": stats}


def apply_folder(folder: str, agreed_path: str, out_folder: str, apply_overflow: bool = False, width_csv: str = "") -> dict:
    """Plan and write every *VN*.xls in folder to out_folder (originals untouched). width_csv lists skipped/flagged rows."""
    from . import sonyxls
    agreed = load_agreed(agreed_path)
    src_dir, out_dir = Path(folder).expanduser(), Path(out_folder).expanduser()
    if src_dir.resolve() == out_dir.resolve():
        raise ValueError("out_folder must differ from folder (never overwrite the originals)")
    report, width_rows = {}, []
    for f in sorted(src_dir.glob("*VN*.xls")):
        p = plan(sonyxls.read_rows(str(f)), agreed, apply_overflow)
        res = sonyxls.write_proposals(str(f), str(out_dir / f.name), p["proposals"], overwrite=True) if p["proposals"] else {}
        report[f.name] = {**p["stats"], "verify_mismatches": res.get("verify_mismatches", 0)}
        width_rows += [{"file": f.name, **s} for s in p["skipped_width"]]
        if apply_overflow:
            width_rows += [{"file": f.name, "row": x["row"], "sid": x["sid"], "agreed": x["an"]}
                           for x in p["proposals"] if x["av"].find("SonyTool") >= 0]
    if width_csv and width_rows:
        with open(Path(width_csv).expanduser(), "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["File", "Row", "S#", "English", "Current", "AGREED", "Max width", "Rows"])
            for x in width_rows:
                lay = x.get("layout") or {}
                w.writerow([x["file"], x["row"], x["sid"], x.get("en", ""), x.get("current", ""), x["agreed"],
                            lay.get("max_w", ""), lay.get("rows", "")])
    return {"files": report, "width_rows": len(width_rows), "out_folder": str(out_dir)}
