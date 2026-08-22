#!/usr/bin/env python3
"""Reopen a workbook and flag unfinished-agent tells.

Checks: leftover Sheet1/Sheet2 names, formula-looking text that is not a
formula, missing freeze panes on the first sheet, and numeric constants
next to a 'Total' label (should be a SUM).

Usage:
  python scripts/qa_workbook.py output.xlsx
"""

from __future__ import annotations

import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
T_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"


def _col_row(cell_ref: str) -> tuple[str, int]:
    letters = "".join(c for c in cell_ref if c.isalpha())
    number = int("".join(c for c in cell_ref if c.isdigit()) or "0")
    return letters, number


def _cell_display(c: ET.Element, shared: list[str]) -> str:
    cell_type = c.get("t")
    v = c.find("m:v", NS)
    if cell_type == "s" and v is not None and v.text and v.text.isdigit():
        idx = int(v.text)
        if idx < len(shared):
            return shared[idx]
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in c.iter(T_NS))
    if v is not None:
        return v.text or ""
    return ""


def _is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


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
                shared.append("".join(t.text or "" for t in si.iter(T_NS)))

        sheet_files = sorted(
            n for n in z.namelist()
            if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
        )
        first_sheet = sheet_files[0] if sheet_files else None

        for name in sheet_files:
            root = ET.fromstring(z.read(name))
            sheet_issues = 0
            formulas = 0
            rows: dict[int, list[tuple[str, str, bool]]] = defaultdict(list)
            for c in root.findall(".//m:c", NS):
                ref = c.get("r", "")
                _, row_n = _col_row(ref)
                f = c.find("m:f", NS)
                has_formula = f is not None
                if has_formula:
                    formulas += 1
                    text = ""
                else:
                    text = _cell_display(c, shared)
                    if text[:1] in {"=", "+", "@"}:
                        print(f"issue: {name} {ref} looks like a formula stored as text: {text!r}")
                        sheet_issues += 1
                rows[row_n].append((ref, text, has_formula))
            if name == first_sheet:
                frozen = any(
                    pane.get("state") in {"frozen", "frozenSplit"}
                    for pane in root.findall(".//m:pane", NS)
                )
                if not frozen:
                    print(f"issue: {name} has no freeze panes")
                    sheet_issues += 1
            for cells in rows.values():
                if not any(text.strip().lower() == "total" for _, text, _ in cells):
                    continue
                for ref, text, has_formula in cells:
                    if has_formula or not text or not _is_number(text):
                        continue
                    print(f"issue: {name} {ref} numeric constant next to a Total label")
                    sheet_issues += 1
            if formulas == 0:
                print(f"issue: {name} has no formulas (totals may be dead values)")
                sheet_issues += 1
            issues += sheet_issues
    print(f"{issues} issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
