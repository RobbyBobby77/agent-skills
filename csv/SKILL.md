---
name: csv
description: >
  Create, clean, validate, merge, and analyze CSV/TSV files. Use when the user
  mentions CSV, TSV, comma-separated data, messy exports, encoding issues,
  delimiter detection, deduping rows, schema checks, or converting between CSV
  and Excel/JSON/Parquet. Prefer this for flat-file data work; use xlsx for
  formatted workbooks and data-analysis for deep EDA/plots.
---

# CSV / TSV

## Related skills

| Need | Skill |
|------|-------|
| Insights, KPIs, charts, experiments | `data-analysis` |
| Spreadsheet deliverable with formulas | `xlsx` |
| Database query | `sql` |

## Workflow

1. Inspect a **byte/sample slice** before loading the entire file; detect encoding, delimiter, quoting, header row, and line endings
2. Preserve the source file; write results to a **new path** unless in-place replacement is explicitly requested
3. State **row identity**, type conversions, null policy, and deduplication key before transforming
4. Apply transforms; keep a reject/quarantine frame for bad rows when quality matters
5. Validate row/column counts, dtypes, and keys; **re-parse** the written output
6. Report output path, schema summary, and every material cleanup decision

## Tool choice

| Task | Tool |
|------|------|
| Load / clean / transform | **pandas** |
| Fast CLI peek | `python -c`, `csvkit`, `xsv` if installed |
| Huge files that don't fit RAM | **polars** scan, or chunked pandas |
| Strict validation | schema dict + dtype checks (below) |
| Analytics after clean | hand off to `data-analysis` |

```bash
pip install pandas polars chardet pyarrow
```

---

## Inspect before load

```python
from pathlib import Path
import chardet
from collections import Counter

path = Path("data.csv")
print("size_mb", path.stat().st_size / 1e6)
raw = path.read_bytes()[:200_000]
print(chardet.detect(raw))

text = raw.decode("utf-8", errors="replace")
lines = text.splitlines()[:5]
for i, line in enumerate(lines):
    print(i, repr(line[:200]))
print(Counter(c for c in lines[0] if c in ",;\t|"))
```

```bash
wc -l data.csv
head -n 5 data.csv | cat -A   # show CR/tabs/weird bytes
```

---

## Read safely

```python
import pandas as pd

df = pd.read_csv(
    "data.csv",
    dtype=str,              # start as strings if types are messy
    keep_default_na=True,
    na_values=["", "NA", "N/A", "null", "None", "-", "#N/A"],
    encoding="utf-8",       # utf-8-sig if BOM; else chardet result
    sep=None,               # sniff delimiter when engine='python'
    engine="python",
    on_bad_lines="warn",    # pandas ≥1.3; inspect warnings
)
# explicit TSV:
# df = pd.read_csv("data.tsv", sep="\t", encoding="utf-8-sig", dtype=str)
```

### Chunked read (large files)

```python
chunks = pd.read_csv("big.csv", chunksize=100_000, dtype=str)
# example: filter early
parts = [c[c["country"] == "US"] for c in chunks]
df = pd.concat(parts, ignore_index=True)
```

### Polars scan

```python
import polars as pl
lf = pl.scan_csv("big.csv", infer_schema_length=10000)
print(lf.collect_schema())
df = lf.filter(pl.col("status") == "paid").collect()
```

---

## Clean checklist

1. **Normalize headers** — strip, snake_case, unique
2. **Trim strings** — whitespace on object columns
3. **Parse dates** — `pd.to_datetime(..., errors="coerce", utc=True)` or explicit format
4. **Numbers** — strip `$`, `,`, spaces → `pd.to_numeric(..., errors="coerce")`
5. **Booleans** — map yes/no/true/false/1/0 consistently
6. **IDs as strings** — preserve leading zeros
7. **Dedupe** — define key columns; `drop_duplicates(subset=keys, keep="last")`
8. **Null policy** — drop vs impute; document choice; quarantine if needed
9. **Categories** — casefold; map aliases (`US`/`USA`/`United States`)
10. **Row identity** — know what one row means (order line vs order vs daily aggregate)

```python
def snake_columns(df):
    cols = (
        df.columns.astype(str).str.strip().str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.strip("_")
    )
    seen = {}
    out = []
    for c in cols:
        if c not in seen:
            seen[c] = 0
            out.append(c)
        else:
            seen[c] += 1
            out.append(f"{c}_{seen[c]}")
    df = df.copy()
    df.columns = out
    return df

df = snake_columns(df)
for c in df.select_dtypes("object"):
    df[c] = df[c].str.strip()
```

### Quarantine bad rows

```python
key = ["order_id"]
bad = df[df["order_id"].isna() | df.duplicated(subset=key, keep=False)]
good = df.drop(index=bad.index)
bad.to_csv("rejects.csv", index=False)
print(len(bad), "rejected", len(good), "kept")
```

---

## Validate

```python
required = ["id", "email", "created_at"]
missing_cols = [c for c in required if c not in df.columns]
assert not missing_cols, missing_cols

bad_email = ~df["email"].fillna("").str.contains(r"^[^@]+@[^@]+\.[^@]+$", regex=True)
dupes = df.duplicated(subset=["id"], keep=False)
report = {
    "rows": len(df),
    "cols": list(df.columns),
    "null_pct": df.isna().mean().round(3).to_dict(),
    "bad_email": int(bad_email.sum()),
    "dup_ids": int(dupes.sum()),
    "id_unique": df["id"].nunique(dropna=True),
}
print(report)
# fail loud on contract breaks when building pipelines
assert report["dup_ids"] == 0, "duplicate ids"
```

### Schema snapshot (for handoff)

```python
schema = pd.DataFrame({
    "column": df.columns,
    "dtype": df.dtypes.astype(str).values,
    "null_pct": df.isna().mean().values,
    "example": [df[c].dropna().astype(str).iloc[0] if df[c].notna().any() else None for c in df.columns],
})
schema.to_csv("schema_summary.csv", index=False)
```

---

## Write

```python
df.to_csv("clean.csv", index=False, encoding="utf-8")
df.to_csv("clean_excel.csv", index=False, encoding="utf-8-sig")  # Excel BOM
df.to_parquet("clean.parquet", index=False)  # preferred for analytics pipelines
```

**Rules**
- Always `index=False` unless index is meaningful data
- Prefer UTF-8; `utf-8-sig` only when Excel users need BOM
- Don't write formulas — CSV is data, not Excel
- Prefer Parquet for large cleaned outputs consumed by Python/polars

### Formula injection (Excel consumers)

When the CSV will be opened in Excel/Sheets, treat untrusted cells starting with `=`, `+`, `-`, or `@` as risky:

```python
def neutralize(val: str) -> str:
    if isinstance(val, str) and val[:1] in "=+-@":
        return "'" + val  # or strip leading char per policy
    return val

for c in df.select_dtypes("object"):
    df[c] = df[c].map(lambda x: neutralize(x) if isinstance(x, str) else x)
```

---

## Merge / join

```python
out = left.merge(right, on="id", how="left", validate="m:1", indicator=True)
print(out["_merge"].value_counts())  # left_only = unmatched
# row count sanity
assert len(out) == len(left), "unexpected fan-out — check keys"
```

Use `validate` (`1:1`, `m:1`, `1:m`) to catch fan-out. Aggregate the many-side before join when analysis needs one row per entity.

---

## Handoff to analysis

After cleaning, leave enough context for `data-analysis`:

```text
file: clean.parquet
grain: one row per order
key: order_id
time col: created_at (UTC)
population: paid orders, test accounts excluded
known issues: 12 rows in rejects.csv (missing order_id)
```

---

## Pitfalls

- Excel “CSV” with `;` delimiters (European locales)
- Mixed line endings / embedded newlines inside quoted fields
- Leading zeros in IDs stripped — read as `dtype=str`
- Dates parsed as US `MM/DD` when data is `DD/MM` — set `dayfirst=True` or `format=`
- Silent truncation of long numerics / long IDs — keep as strings
- Headerless files / extra title rows — use `header=` / `skiprows=`
- Duplicate column names after bad exports
- Assuming `wc -l` equals data rows (header + broken quotes)
