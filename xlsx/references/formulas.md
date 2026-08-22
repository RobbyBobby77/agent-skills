# Excel Formulas Agents Should Prefer

Write formulas so the workbook recalculates when inputs change.

## Essentials

| Need | Formula |
|------|---------|
| Sum range | `=SUM(E3:E100)` |
| Conditional sum | `=SUMIF(A3:A100,"EMEA",E3:E100)` |
| Multi-condition sum | `=SUMIFS(E3:E100,A3:A100,"EMEA",C3:C100,"Pro")` |
| Count | `=COUNTA(A3:A100)` / `=COUNTIF(...)` |
| Average | `=AVERAGE(E3:E100)` |
| Lookup (modern) | `=XLOOKUP(H3,A3:A100,E3:E100,"")` |
| Lookup (legacy) | `=VLOOKUP(H3,A3:E100,5,FALSE)` |
| Index/Match | `=INDEX(E3:E100,MATCH(H3,A3:A100,0))` |
| IF | `=IF(F3>=0.4,"Healthy","Watch")` |
| Nested / IFS | `=IFS(F3>=0.5,"A",F3>=0.4,"B",TRUE,"C")` |
| Error guard | `=IFERROR(XLOOKUP(...),"")` |
| Unique list | `=UNIQUE(A3:A100)` |
| Filter spill | `=FILTER(A3:E100,A3:A100="EMEA")` |
| Sort | `=SORT(A3:E100,5,-1)` |
| Today | `=TODAY()` / `=NOW()` |
| Text join | `=TEXTJOIN(", ",TRUE,A3:A10)` |

## Dynamic totals (tables)

If you convert a range to a Table (`Table` in openpyxl), use structured refs:

```
=SUM(Table1[Revenue])
=SUMIF(Table1[Region],"NA",Table1[Revenue])
```

## Running balance

```
// row 3 is first data row; column G is Amount, H is Balance
H3: =G3
H4: =H3+G4   // fill down
```

## Percentage of total

```
=E3/$E$101   // absolute row on total
```

## Cross-sheet

```
=Summary!B2
='Raw Data'!B2
=SUM('Raw Data'!E:E)
```

## Don't

- Hardcode a total you already have as a range
- Use `VLOOKUP` when column order may change — prefer `XLOOKUP` / `INDEX-MATCH`
- Leave `#DIV/0!` visible — wrap with `IFERROR` or guard denominators
- Copy formula results as values unless the user wants a snapshot
