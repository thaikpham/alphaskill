#!/usr/bin/env python3
"""Export public data from private data dir: drop internal references, empty TM."""
import json
import argparse
import re
from pathlib import Path

def export_public_data(src_dir: Path, out_dir: Path):
    """Copy data from src to out, filtering for public release."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. tm.jsonl: empty file
    (out_dir / "tm.jsonl").write_text("")

    # 2. feedback.jsonl: empty file
    (out_dir / "feedback.jsonl").write_text("")

    # 3. glossary.json: keep only en, vi, short, category, locked, note (drop S-numbers from note)
    glossary_in = json.loads((src_dir / "glossary.json").read_text(encoding="utf-8")) if (src_dir / "glossary.json").exists() else []
    glossary_out = []
    for entry in glossary_in:
        out_entry = {
            "en": entry.get("en", ""),
            "vi": entry.get("vi", ""),
        }
        if entry.get("short"):
            out_entry["short"] = entry["short"]
        if entry.get("category"):
            out_entry["category"] = entry["category"]
        if entry.get("locked"):
            out_entry["locked"] = entry["locked"]

        # Drop note if it contains S-number (S\d{5,})
        note = entry.get("note", "")
        if note and not re.search(r"S\d{5,}", note):
            out_entry["note"] = note

        glossary_out.append(out_entry)

    (out_dir / "glossary.json").write_text(json.dumps(glossary_out, ensure_ascii=False, indent=1), encoding="utf-8")

    # 4. rules.json: keep substitutions (reset learned_from/hits/count) and banned; exact = {}
    rules_in = json.loads((src_dir / "rules.json").read_text(encoding="utf-8")) if (src_dir / "rules.json").exists() else {"substitutions": [], "exact": {}, "banned": []}

    rules_out = {
        "substitutions": [],
        "exact": {},
        "banned": rules_in.get("banned", [])
    }

    for sub in rules_in.get("substitutions", []):
        out_sub = {k: v for k, v in sub.items() if k not in ("learned_from", "hits", "count")}
        out_sub["hits"] = 0
        out_sub["count"] = 0
        rules_out["substitutions"].append(out_sub)

    (out_dir / "rules.json").write_text(json.dumps(rules_out, ensure_ascii=False, indent=1), encoding="utf-8")

    # 5. exceptions.json: copy as is
    if (src_dir / "exceptions.json").exists():
        exceptions = json.loads((src_dir / "exceptions.json").read_text(encoding="utf-8"))
        (out_dir / "exceptions.json").write_text(json.dumps(exceptions, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        (out_dir / "exceptions.json").write_text("{}", encoding="utf-8")

    # 6. keep_english.json: copy as is
    if (src_dir / "keep_english.json").exists():
        keep = json.loads((src_dir / "keep_english.json").read_text(encoding="utf-8"))
        (out_dir / "keep_english.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        (out_dir / "keep_english.json").write_text("[]", encoding="utf-8")

    # 7. rules.md: copy as is
    if (src_dir / "rules.md").exists():
        rules_md = (src_dir / "rules.md").read_text(encoding="utf-8")
        (out_dir / "rules.md").write_text(rules_md, encoding="utf-8")

    print(f"✓ Exported public data to {out_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export public data from private data dir")
    parser.add_argument("--src", required=True, help="Source data directory")
    parser.add_argument("--out", required=True, help="Output data directory")
    args = parser.parse_args()

    export_public_data(Path(args.src), Path(args.out))
