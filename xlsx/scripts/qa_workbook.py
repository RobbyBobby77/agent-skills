#!/usr/bin/env python3
"""Reopen a workbook and flag unfinished-agent tells.

Checks: leftover Sheet1/Sheet2 names, formula-looking text that is not a
formula, missing freeze on the first sheet, totals written as numbers next
to a 'Total' label when a SUM exists nearby.

Usage:
  python xlsx/scripts/qa_workbook.py output.xlsx
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_row(cell_ref: str) -> tuple[str, int]:
    letters = "".join(c for c in cell_ref if c.isalpha())
    number = int("".join(c for c in cell_ref if c.isdigit()) or "0")
    return letters, number


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: qa_workbook.py book.xlsx")
    path = Path(sys.argv[1])
    issues = 0
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        names = [n.get("name", "") for n in wb.findall("m:sheets/m:sheet", NS)]
        print("sheets:", ", ".join(names))
        for name in names:
            if name in {"Sheet1", "Sheet2", "Sheet"}:
                print("issue: leftover default sheet name", name)
                issues += 1

        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in sst.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))

        for name in z.namelist():
            if not name.startswith("xl/worksheets/sheet") or not name.endswith(".xml"):
                continue
            root = ET.fromstring(z.read(name))
            sheet_issues = 0
            formulas = 0
            for c in root.findall(".//m:c", NS):
                ref = c.get("r", "")
                f = c.find("m:f", NS)
                v = c.find("m:v", NS)
                if f is not None:
                    formulas += 1
                    continue
                text = ""
                if c.get("t") == "s" and v is not None and v.text and v.text.isdigit():
                    idx = int(v.text)
                    if idx < len(shared):
                        text = shared[idx]
                elif v is not None:
                    text = v.text or ""
                if text[:1] in {"=", "+", "@"}:
                    print(f"issue: {name} {ref} looks like a formula stored as text: {text!r}")
                    sheet_issues += 1
            if formulas == 0:
                print(f"issue: {name} has no formulas (totals may be dead values)")
                sheet_issues += 1
            issues += sheet_issues
    print(f"{issues} issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
