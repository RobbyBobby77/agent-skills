# Excel Formatting Cheatsheet (openpyxl)

## Fonts & fills

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection

title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
body = Font(name="Calibri", size=11, color="111827")
link = Font(name="Calibri", size=11, color="2563EB", underline="single")

dark = PatternFill("solid", fgColor="0F172A")
brand = PatternFill("solid", fgColor="1F4E79")
zebra = PatternFill("solid", fgColor="F8FAFC")
warn = PatternFill("solid", fgColor="FEF3C7")
bad = PatternFill("solid", fgColor="FEE2E2")
good = PatternFill("solid", fgColor="DCFCE7")
```

Colors are **6-char RGB without `#`**.

## Borders

```python
thin = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)
thick_bottom = Border(bottom=Side(style="medium", color="1F4E79"))
```

## Number formats

```python
cell.number_format = '"$"#,##0.00'     # money
cell.number_format = '#,##0'           # integer with thousands
cell.number_format = '0.0%'            # percent (store 0.42, not 42)
cell.number_format = 'YYYY-MM-DD'      # date
cell.number_format = 'YYYY-MM-DD HH:MM'
cell.number_format = '0.00'            # decimal
cell.number_format = '#,##0;(#,##0);"—"'  # accounting-ish
```

## Alignment & row height

```python
cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws.row_dimensions[1].height = 28
ws.column_dimensions["A"].width = 18
# rough auto-width
for col in ws.columns:
    letter = col[0].column_letter
    width = max((len(str(c.value)) if c.value else 0) for c in col)
    ws.column_dimensions[letter].width = min(max(width + 2, 10), 48)
```

## Freeze, filter, print

```python
ws.freeze_panes = "A2"                 # freeze row 1
ws.auto_filter.ref = "A1:F500"
ws.print_title_rows = "1:1"            # repeat header when printing
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToPage = True
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
```

## Tables (recommended for data ranges)

```python
from openpyxl.worksheet.table import Table, TableStyleInfo

tab = Table(displayName="Sales", ref=f"A2:F{last_row}")
tab.tableStyleInfo = TableStyleInfo(
    name="TableStyleMedium2", showRowStripes=True, showFirstColumn=False,
)
ws.add_table(tab)
```

## Data validation (dropdowns)

```python
from openpyxl.worksheet.datavalidation import DataValidation

dv = DataValidation(type="list", formula1='"EMEA,NA,APAC"', allow_blank=True)
dv.error = "Pick a region"
dv.errorTitle = "Invalid"
ws.add_data_validation(dv)
dv.add(f"A3:A{last_row}")
```

## Conditional formatting

```python
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule, FormulaRule

ws.conditional_formatting.add("E3:E100", ColorScaleRule(
    start_type="min", start_color="FCA5A5",
    mid_type="percentile", mid_value=50, mid_color="FDE68A",
    end_type="max", end_color="86EFAC",
))

ws.conditional_formatting.add("F3:F100", CellIsRule(
    operator="lessThan", formula=["0.35"],
    fill=PatternFill("solid", fgColor="FEE2E2"),
))
```

## Protection

```python
ws["B2"].protection = Protection(locked=False)  # input cell
ws.protection.sheet = True
ws.protection.password = "<sheet-password>"
```

## Named styles (reuse)

```python
from openpyxl.styles import NamedStyle
hdr = NamedStyle(name="hdr")
hdr.font = header
hdr.fill = brand
hdr.alignment = Alignment(horizontal="center")
wb.add_named_style(hdr)
ws["A2"].style = "hdr"
```
