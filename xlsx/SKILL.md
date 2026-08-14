---
name: xlsx
description: >
  Create, read, edit, and analyze Excel workbooks (.xlsx, .xlsm). Use when the user
  mentions Excel, spreadsheet, .xlsx, workbook, pivot, formulas, budgets, financial
  models, CSV-to-Excel, dashboards in sheets, or tabular data deliverables. Covers
  openpyxl/xlsxwriter creation, pandas analysis, formatting, validation, charts,
  and formula hygiene. Do NOT use for Word docs, PowerPoint, or pure PDF tasks.
---

# Excel (XLSX)

## Related skills

| Need | Skill |
|------|-------|
| Flat-file cleanup / injection | `csv` |
| Insights rather than a workbook | `data-analysis` |
| Word / slides / PDF | `docx` / `pptx` / `pdf` |

## Workflow

1. Preserve the input and inspect sheets, dimensions, formulas, names, tables, charts, validation, hidden content, and macros.
2. Decide whether formulas, cached values, styles, external links, and VBA must survive.
3. Make targeted edits and write a new workbook by default; avoid restyling unrelated cells.
4. Reopen with `data_only=False`, validate formulas/ranges and workbook structure, then render or open for visual QA.
5. Report recalculation limitations and anything the chosen library could not preserve.

## Tool choice

| Task | Tool |
|------|------|
| Analyze / transform data | **pandas** (+ openpyxl engine) |
| Create formatted workbooks | **openpyxl** (or xlsxwriter for write-heavy) |
| Read values (computed) | Excel isn't here — use pandas for values, or formulas only when user will open in Excel |
| Charts in-file | openpyxl charts |
| Huge dumps (>100k rows) | pandas → csv, or xlsxwriter constant_memory |
| Advanced `.xlsm` fidelity | Native Excel automation when available |

```bash
pip install openpyxl xlsxwriter pandas
```

---

## Read

```python
import pandas as pd
from openpyxl import load_workbook

# Data
df = pd.read_excel("book.xlsx", sheet_name="Sales")          # first sheet if omitted
all_sheets = pd.read_excel("book.xlsx", sheet_name=None)     # dict of DataFrames

# Workbook structure / formulas / styles
wb = load_workbook("book.xlsx", data_only=False)
print(wb.sheetnames)
ws = wb["Sales"]
print(ws["A1"].value, ws["B2"].value)
```

`data_only=True` returns cached computed values — **only if Excel/LibreOffice has opened and saved the file**. Freshly written formulas return `None` with `data_only=True`.

For basic `.xlsm` edits, use `load_workbook(..., keep_vba=True)` and save as `.xlsm`; otherwise
macros can be lost. This does not guarantee preservation of ActiveX, slicers, Power Query, digital
signatures, advanced charts, or every external-link feature. Use native Excel automation for a
feature-rich workbook when exact round-trip fidelity matters, disable macros while opening, and do
not refresh external connections unless requested.

Editing a digitally signed workbook invalidates the signature; flag this before making changes.

### What this stack will not preserve

| Feature | openpyxl / xlsxwriter |
|---------|------------------------|
| Cell values, most formulas, basic styles | Yes |
| Tables, data validation, freeze, autofilter | Usually |
| VBA / macros | Only with `keep_vba=True` and `.xlsm` |
| Pivot caches, Power Query, slicers, ActiveX | No — use Excel |
| Digital signatures | Invalidated by any write |
| Cached formula results | Not computed until Excel/LibreOffice recalculates |

---

## Create a polished workbook (openpyxl)

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Fill, PatternFill, Alignment, Border, Side, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
from openpyxl.worksheet.table import Table, TableStyleInfo
import pandas as pd

wb = Workbook()
ws = wb.active
ws.title = "Dashboard"

# --- styles ---
title_font = Font(name="Calibri", size=18, bold=True, color="FFFFFF")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
body_font = Font(name="Calibri", size=11, color="1F2937")
money_font = Font(name="Calibri", size=11, color="1F2937")
header_fill = PatternFill("solid", fgColor="1F4E79")
title_fill = PatternFill("solid", fgColor="0F172A")
alt_fill = PatternFill("solid", fgColor="F1F5F9")
thin = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)

# Title band
ws.merge_cells("A1:F1")
ws["A1"] = "Q3 Sales Dashboard"
ws["A1"].font = title_font
ws["A1"].fill = title_fill
ws["A1"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
ws.row_dimensions[1].height = 32

# Headers
headers = ["Region", "Rep", "Product", "Units", "Revenue", "Margin %"]
for col, h in enumerate(headers, 1):
    cell = ws.cell(2, col, h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin

data = [
    ("EMEA", "Ada", "Pro", 120, 48000, 0.42),
    ("EMEA", "Bea", "Basic", 200, 30000, 0.35),
    ("NA", "Cam", "Pro", 150, 60000, 0.45),
    ("NA", "Dan", "Enterprise", 40, 80000, 0.51),
    ("APAC", "Eve", "Basic", 180, 27000, 0.33),
]

for r, row in enumerate(data, 3):
    for c, val in enumerate(row, 1):
        cell = ws.cell(r, c, val)
        cell.font = body_font
        cell.border = thin
        if r % 2 == 1:
            cell.fill = alt_fill
        if c == 5:
            cell.number_format = '"$"#,##0'
        if c == 6:
            cell.number_format = "0.0%"

last_row = 2 + len(data)

# Totals with formulas (not hardcoded)
ws.cell(last_row + 1, 3, "Total").font = Font(bold=True)
ws.cell(last_row + 1, 4, f"=SUM(D3:D{last_row})").font = Font(bold=True)
ws.cell(last_row + 1, 5, f"=SUM(E3:E{last_row})").font = Font(bold=True)
ws.cell(last_row + 1, 5).number_format = '"$"#,##0'

# Column widths (don't leave defaults)
widths = [12, 10, 14, 10, 14, 12]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# Freeze header
ws.freeze_panes = "A3"

# Auto filter
ws.auto_filter.ref = f"A2:F{last_row}"

# Conditional formatting on margin
ws.conditional_formatting.add(
    f"F3:F{last_row}",
    ColorScaleRule(start_type="min", start_color="FCA5A5",
                   mid_type="percentile", mid_value=50, mid_color="FDE68A",
                   end_type="max", end_color="86EFAC"),
)

# Chart
chart = BarChart()
chart.type = "col"
chart.title = "Revenue by Row"
chart.y_axis.title = None
chart.x_axis.title = None
chart.style = 10
data_ref = Reference(ws, min_col=5, min_row=2, max_row=last_row)
cats = Reference(ws, min_col=1, min_row=3, max_row=last_row)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats)
chart.shape = 4
chart.height = 8
chart.width = 12
ws.add_chart(chart, "H2")

# Second sheet from DataFrame
ws2 = wb.create_sheet("Raw")
df = pd.DataFrame(data, columns=headers)
for r in dataframe_to_rows(df, index=False, header=True):
    ws2.append(r)
for cell in ws2[1]:
    cell.font = header_font
    cell.fill = header_fill

wb.save("output.xlsx")
```

More patterns: [references/formulas.md](references/formulas.md), [references/formatting.md](references/formatting.md)

---

## Critical rules

1. **Formulas over hardcoded totals** — `=SUM()`, `=XLOOKUP()`, `=IF()` so the sheet stays live
2. **Number formats** — currency, percent, dates; never leave 0.42 looking like a raw float when it's a %
3. **Set column widths** — default widths look unfinished
4. **Freeze header rows** — `ws.freeze_panes = "A2"` (cell below/right of freeze)
5. **One header row, contiguous data** — required for filters/tables/pivots
6. **Don't mix types in a column** — numbers as numbers, not strings
7. **Dates as real dates** — `datetime` objects + `number_format = "YYYY-MM-DD"`, not strings
8. **No merged cells in data ranges** — merge only titles/labels
9. **Readable sheet names** — `"Sales 2026"` not `"Sheet1"`
10. **Text wrap + alignment** for long headers; vertical center for tables
11. **Validate assumptions** — data validation dropdowns for categories when building input sheets
12. **Never put secrets in workbooks** casually; strip credentials before sharing
13. **Treat untrusted text as text** — prefix `=`, `+`, `@`, and non-numeric `-` (same rule as `csv`). Real negative numbers stay numbers.

### Formula gotchas

- Write formulas as strings starting with `=`: `cell.value = "=A1+B1"`
- Use commas in formulas for Excel compatibility (`=IF(A1>0,1,0)`); openpyxl writes what you give it
- Cross-sheet: `=Sales!E3` or `='Sheet Name'!E3`
- After write, values aren't computed until Excel/LibreOffice recalculates

### LibreOffice recalculation (optional headless)

`xlsx → xlsx` often keeps stale cached values (a `SUM` stays `0`). Round-trip through Calc's native format:

```bash
python scripts/soffice.py --convert-to ods --outdir tmp output.xlsx
python scripts/soffice.py --convert-to xlsx --outdir recalculated tmp/output.ods
# or open and save once in Excel; verify the converted output before replacing anything
```

`scripts/soffice.py` finds `soffice` on PATH or the official Flatpak. Do not assume `soffice` is on PATH.

---

## pandas ↔ Excel

```python
# Write multi-sheet
with pd.ExcelWriter("out.xlsx", engine="openpyxl") as xw:
    sales.to_excel(xw, sheet_name="Sales", index=False)
    summary.to_excel(xw, sheet_name="Summary", index=False)

# Append / style after pandas dump
from openpyxl import load_workbook
wb = load_workbook("out.xlsx")
ws = wb["Sales"]
ws.freeze_panes = "A2"
# ... apply styles ...
wb.save("out.xlsx")
```

---

## Editing existing files

```python
wb = load_workbook("template.xlsx")
ws = wb.active
ws["B2"] = 42
ws["C2"] = "=B2*1.2"
# Insert rows carefully — update formulas if needed
ws.insert_rows(5)
wb.save("edited.xlsx")
```

Preserve existing styles when doing light edits: copy `cell.font` / `fill` from neighbors rather than restyling the whole sheet unless asked.

Do not overwrite the original until the candidate has been reopened and structurally compared.
Keep a recoverable backup for replacement workflows unless the user explicitly declines one.

---

## QA checklist

```bash
python scripts/qa_workbook.py output.xlsx
```

- [ ] Headers frozen, filter on
- [ ] Currency/percent/date formats applied
- [ ] Column widths fit content (not 50 chars of ####)
- [ ] Totals are formulas
- [ ] No `Sheet1` / `Sheet2` leftovers
- [ ] Charts reference the correct range (include new rows or use tables)
- [ ] Print area / page setup if user will print
- [ ] No `#REF!`, `#N/A`, circular refs introduced

---

## Dependencies

```bash
pip install openpyxl xlsxwriter pandas
# optional: formulas, style helpers
pip install formulas  # evaluate some Excel formulas in pure Python when needed
```
