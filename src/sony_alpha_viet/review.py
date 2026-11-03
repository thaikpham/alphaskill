"""Review a folder of Sony *TranslationCheck_VN.xls files: audit the effective string of every row and find real inconsistencies."""
from __future__ import annotations

import csv
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from . import core

DUMMY = "<c0000>"
ORDER = ["token_mismatch", "line_count", "not_nfc", "english_residue", "banned", "exact_rule", "FIT:OVER", "locked_term", "tm_diff",
         "variant_word_choice", "missing_period", "an_without_au_av"]


def norm(text: str) -> str:
    """Group key: icons/variables → ◆, spaces collapsed (case kept; callers lower() the EN side)."""
    return re.sub(r"\s+", " ", core.TOKEN_RE.sub("◆", text or "")).strip()


def effective(row: dict) -> str:
    """The string under review: AN (our proposal) if set, else VI (Sony's current text). Reviewing VI alone is wrong."""
    return core.nfc(row["an"] if row["an"].strip() else row["vi"])


def word_choice_variants(rows: list[dict]) -> list[tuple[dict, str]]:
    """Rows whose translation differs from the majority for the same EN although the majority would fit their frame.
    A shorter form in a narrower frame is a valid abbreviation and is not returned. rows need en, layout, eff."""
    body = lambda t: norm(core.ICON_PREFIX_RE.match(t).group(2))
    groups = defaultdict(list)
    for r in rows:
        groups[body(r["en"]).lower()].append(r)
    out = []
    for rs in groups.values():
        votes = Counter(body(r["eff"]) for r in rs)
        if len(votes) < 2:
            continue
        major = votes.most_common(1)[0][0]
        for r in rs:
            if body(r["eff"]) == major:
                continue
            lay = core.effective_layout(r["en"], r["layout"])
            trial = core.ICON_PREFIX_RE.match(r["eff"]).group(1) + major.replace("◆", DUMMY)
            if core.fit(trial, **lay)["verdict"] in ("OK", "BORDER"):
                out.append((r, major))
    return out


def review_folder(folder: str, out_csv: str = "") -> dict:
    """Audit every *TranslationCheck_VN.xls in folder (strict: approved memory is re-checked too)."""
    from .xls import sonyxls
    store = core.Store()
    tm = {}
    for e in store.tm:
        tm.setdefault(e["id"], e)
    files = sorted(Path(folder).glob("*TranslationCheck_VN.xls"))
    rows, found = [], []
    for f in files:
        for r in sonyxls.read_rows(str(f)):
            r["file"], r["eff"] = f.name, effective(r)
            rows.append(r)

    def add(kind, r, detail=""):
        found.append({"type": kind, "file": r["file"], "row": r["row"], "sid": r["sid"], "en": r["en"], "vi": r["vi"], "an": r["an"],
                      "eff": r["eff"], "detail": detail})

    for r in rows:
        a = core.audit(store, r["en"], r["eff"], r["layout"], strict=True)
        for i in a["issues"]:
            if i.get("severity") != "info" and i["type"] not in ("layout_suspect", "inconsistent_with_memory"):
                add(i["type"], r, {k: v for k, v in i.items() if k not in ("type", "severity")})
        if a.get("fit", {}).get("verdict") == "OVER":
            add("FIT:OVER", r, {"ratio": a["fit"].get("ratio")})
        t = tm.get(r["sid"])
        if t and core.nfc(t["vi"]) != r["eff"]:
            add("tm_diff", r, {"tm_vi": t["vi"]})
        if r["an"].strip() and not (r["au"].strip() and r["av"].strip()):
            add("an_without_au_av", r)
    for r, major in word_choice_variants(rows):
        add("variant_word_choice", r, {"majority": major})

    rank = {k: i for i, k in enumerate(ORDER)}
    found.sort(key=lambda x: (rank.get(x["type"], len(ORDER)), x["file"], x["row"]))
    if out_csv:
        os.makedirs(os.path.dirname(os.path.abspath(out_csv)), exist_ok=True)
        with open(out_csv, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["type", "file", "row", "sid", "en", "vi", "an", "eff", "detail"])
            w.writeheader()
            w.writerows(found)
    return {"files": [f.name for f in files], "rows": len(rows), "counts": dict(Counter(x["type"] for x in found)),
            "by_file": dict(Counter(x["file"] for x in found)), "top": found[:40], **({"csv": out_csv} if out_csv else {})}
