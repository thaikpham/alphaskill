"""Human review sheet for a set of Sony *_TranslationCheck_VN.xls files.

Unique English–Vietnamese pairs (Vietnamese = AN when proposed, else AD), written as a two-column .xlsx with two tabs
("Cần dịch", "Giữ nguyên tiếng Anh"), plus a JSON mapping {tab: [{sheet_row, en, vi, rows: [[file, row, S#]]}]} used to
apply the reviewers' edits back to every row. Stdlib only, so it runs without openpyxl.

    alphaskill review-pairs <folder with *_VN.xls> <out.xlsx> <mapping.json>
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.sax.saxutils import escape

TAB_TODO, TAB_KEEP = "Cần dịch", "Giữ nguyên tiếng Anh"
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _nfc(s) -> str:
    return unicodedata.normalize("NFC", str(s or "")).replace("\r\n", "\n").strip("\n")


def _same(en: str, vi: str) -> bool:
    return re.sub(r"\s+", " ", en).strip() == re.sub(r"\s+", " ", vi).strip()


def build_pairs(rows: list[dict]) -> dict:
    """rows: dicts with en, vi (AD), an, row, sid and optionally file. First-occurrence order is kept so related menu
    items and help texts stay together."""
    pairs: OrderedDict = OrderedDict()
    for r in rows:
        en, vi = _nfc(r["en"]), _nfc(r.get("an") or r.get("vi"))
        pairs.setdefault((en, vi), []).append([r.get("file", ""), r["row"], r["sid"]])
    tabs = {TAB_TODO: [], TAB_KEEP: []}
    for (en, vi), rs in pairs.items():
        tab = tabs[TAB_KEEP if _same(en, vi) else TAB_TODO]
        tab.append({"sheet_row": len(tab) + 2, "en": en, "vi": vi, "rows": rs})
    return tabs


def _cell(ref: str, text: str, style: int) -> str:
    return f'<c r="{ref}" t="inlineStr" s="{style}"><is><t xml:space="preserve">{escape(_CTRL.sub("", text))}</t></is></c>'


def _sheet(items: list[dict]) -> str:
    rows = [f'<row r="1">{_cell("A1", "English", 1)}{_cell("B1", "Vietnamese", 1)}</row>']
    rows += [f'<row r="{i}">{_cell(f"A{i}", it["en"], 2)}{_cell(f"B{i}", it["vi"], 2)}</row>'
             for i, it in ((it["sheet_row"], it) for it in items)]
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
            '</sheetView></sheetViews><cols><col min="1" max="2" width="60" customWidth="1"/></cols>'
            f'<sheetData>{"".join(rows)}</sheetData></worksheet>')


def write_xlsx(path: str | Path, tabs: dict) -> None:
    names = list(tabs)
    ns = "http://schemas.openxmlformats.org"
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{ns}/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><name val="Arial"/></font></fonts>'
              '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
              '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="3"><xf/>'
              '<xf fontId="1" applyFont="1"/><xf applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf></cellXfs></styleSheet>')
    workbook = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{ns}/spreadsheetml/2006/main" '
                f'xmlns:r="{ns}/officeDocument/2006/relationships"><sheets>'
                + "".join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, n in enumerate(names, 1))
                + "</sheets></workbook>")
    rels = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}/package/2006/relationships">'
            + "".join(f'<Relationship Id="rId{i}" Type="{ns}/officeDocument/2006/relationships/worksheet" '
                      f'Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(names) + 1))
            + f'<Relationship Id="rId{len(names) + 1}" Type="{ns}/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>")
    types = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="{ns}/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
             + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                       'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                       for i in range(1, len(names) + 1))
             + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
             "</Types>")
    root = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", root)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", rels)
        z.writestr("xl/styles.xml", styles)
        for i, n in enumerate(names, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet(tabs[n]))


def rows_from_folder(folder: str | Path) -> list[dict]:
    from . import sonyxls
    rows = []
    for f in sorted(Path(folder).glob("*TranslationCheck_VN.xls")):
        for r in sonyxls.read_rows(str(f)):
            r["file"] = f.name
            rows.append(r)
    return rows


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[-1].strip())
        return 2
    folder, out_xlsx, mapping = argv
    tabs = build_pairs(rows_from_folder(folder))
    write_xlsx(out_xlsx, tabs)
    Path(mapping).write_text(json.dumps(tabs, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({n: len(v) for n, v in tabs.items()}, ensure_ascii=False),
          "rows", sum(len(it["rows"]) for v in tabs.values() for it in v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
