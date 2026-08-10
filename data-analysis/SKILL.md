---
name: data-analysis
description: >
  Exploratory data analysis (EDA), metric definition, aggregation, statistical
  summaries, charts, cohort/funnel analysis, and basic experiment readouts with
  pandas, polars, matplotlib/plotly/seaborn. Use when the user wants insights from
  datasets, KPI reports, visualizations, A/B summaries, notebook-style investigation,
  or reproducible analytical deliverables. Prefer csv/xlsx for pure file conversion;
  sql for warehouse queries; this skill for interpreting and communicating results.
---

# Data Analysis

## Related skills

| Need | Skill |
|------|-------|
| Messy flat files, encoding, joins | `csv` |
| Warehouse / production SQL | `sql` |
| Formatted Excel deliverable | `xlsx` |
| Stakeholder slides / PDF | `pptx` / `pdf` / `markdown` |

## Workflow

1. **Frame** — restate the decision or question, audience, unit of analysis, population, time zone, and success metric
2. **Define metrics** — write definitions before computing (see [references/metrics.md](references/metrics.md))
3. **Load** — preserve source data; record shape, dtypes, provenance, grain, and time range
4. **Clean** — nulls, types, outliers, dupes with an explicit policy (see `csv` skill)
5. **Validate** — row counts, uniqueness of keys, referential joins, impossible values
6. **Explore** — distributions, segments, correlations; check denominators and coverage
7. **Answer** — one clear question per chart/table; reproduce every quoted number from code
8. **Stress-test** — ask what would flip the conclusion (see [references/gotchas.md](references/gotchas.md))
9. **Report** — observations vs interpretations; filters, assumptions, limitations, next checks

**Hard rules**
- Do not imply causation from observational data
- Never silently drop inconvenient rows or outliers
- Prefer definitions over pretty charts
- If the data cannot answer the question, say so and propose what would

```bash
pip install pandas polars matplotlib seaborn plotly pyarrow scipy statsmodels
```

---

## Define before you compute

Before any groupby, write (even briefly):

```text
Metric: weekly active users (WAU)
Grain: user-week
Numerator: users with ≥1 session in the ISO week
Denominator: n/a (count metric)
Population: non-internal accounts
Time: America/Los_Angeles, weeks Mon–Sun
Filters: status != banned
Caveats: session table only; excludes API-only clients
```

If stakeholders disagree on the definition, stop and align — wrong metric is worse than no chart.

Full template and KPI hygiene: [references/metrics.md](references/metrics.md)

---

## Fast EDA

```python
import pandas as pd

df = pd.read_parquet("events.parquet")  # or read_csv / read_excel
print(df.shape)
print(df.dtypes)
print(df.head())
print(df.describe(include="all").T)
print(df.isna().mean().sort_values(ascending=False).head(20))
print(df.duplicated().sum())

# grain / key checks
print(df["user_id"].nunique(), "users")
print(df.groupby(["user_id", "event_id"]).size().max(), "max dups on key")
```

### Convert types early

```python
df["ts"] = pd.to_datetime(df["ts"], utc=True)
df["revenue_cents"] = pd.to_numeric(df["revenue_cents"], errors="coerce")
df["country"] = df["country"].astype("category")
```

### Coverage checklist

```python
print("date range", df["ts"].min(), "→", df["ts"].max())
print("null revenue", df["revenue_cents"].isna().mean())
print("rows/day", df.groupby(df["ts"].dt.date).size().describe())
# sudden zeros often mean pipeline breaks, not true zeros
```

---

## Groupbys that answer questions

```python
# revenue by week (timezone-aware → local period if needed)
weekly = (
    df.dropna(subset=["ts", "revenue_cents"])
      .assign(week=lambda x: x["ts"].dt.to_period("W").dt.start_time)
      .groupby("week", as_index=False)["revenue_cents"].sum()
)

# top products
df.groupby("sku", observed=True)["revenue_cents"].sum().nlargest(10)

# funnel (ordered steps — verify step order is real, not lexical)
step_order = ["view", "cart", "checkout", "paid"]
funnel = (
    df.groupby("step", observed=True)["user_id"].nunique()
      .reindex(step_order)
)
conversion = funnel / funnel.iloc[0]
```

### Retention / cohort sketch

```python
df["cohort"] = df.groupby("user_id")["ts"].transform("min").dt.to_period("M")
df["month"] = df["ts"].dt.to_period("M")
counts = (
    df.groupby(["cohort", "month"])["user_id"]
      .nunique()
      .unstack(fill_value=0)
)
# rates: divide each row by that cohort's size at month 0
# (first column with activity for each cohort — safer than assuming the diagonal)
sizes = counts.replace(0, pd.NA).bfill(axis=1).iloc[:, 0]
retention = counts.div(sizes, axis=0)
```

### Comparison hygiene

```python
# like-for-like: same length windows, same population filters
a = df[df["ts"].between(start_a, end_a)]
b = df[df["ts"].between(start_b, end_b)]
# prefer MoM/YoY on calendar-aligned periods; flag unequal days (Feb, leap)
```

---

## Plotting

### Matplotlib / seaborn (static — PDF/PPTX friendly)

```python
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", context="talk")
fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=weekly, x="week", y="revenue_cents", ax=ax)
ax.set_title("Weekly revenue")
ax.set_xlabel("")
ax.set_ylabel("Revenue (cents)")
fig.tight_layout()
fig.savefig("weekly_revenue.png", dpi=150)
plt.close()
```

### Plotly (interactive HTML)

```python
import plotly.express as px
fig = px.bar(top, x="sku", y="revenue_cents", title="Top SKUs")
fig.write_html("top_skus.html")
fig.write_image("top_skus.png")  # needs kaleido
```

**Chart rules**
- Label axes and units; include date range in title or subtitle
- Sort bars by value unless category order is meaningful
- ≤6 series or facet; avoid rainbow spaghetti
- Start y at 0 for bar charts (except clearly annotated indexes)
- Export PNG for slides/docs; keep the code that produced the number

Recipes: [references/charts.md](references/charts.md)

---

## Stats sanity

```python
s = df["revenue_cents"].dropna()
print(s.quantile([0.5, 0.9, 0.99, 0.999]))
print("mean vs median", s.mean(), s.median())  # skew signal
```

Always report with a number:
- **n** (and % of population if filtered)
- **date range** and timezone
- **filters** applied
- for rates: **numerator and denominator**
- for comparisons: **baseline definition** and whether periods are equal length

Outlier gates are for visualization or separate “trimmed” metrics — never replace the primary metric without labeling it.

---

## Experiments (A/B) — when asked

Agents should not overclaim significance. Minimum bar:

1. Confirm unit of randomization (user, session, order) matches the analysis unit
2. Check sample ratio mismatch (expected 50/50 vs observed)
3. Primary metric pre-declared; guardrails listed (latency, refunds, complaints)
4. Report effect size + uncertainty, not p-value alone
5. Watch for peeking, multiple comparisons, novelty effects, and bot traffic

Practical readout patterns: [references/experiments.md](references/experiments.md)

```python
# crude directionality only — not a full experimental platform
import numpy as np

def mean_by_variant(df, metric, variant_col="variant"):
    return df.groupby(variant_col)[metric].agg(["count", "mean", "std"])

# bootstrap CI for difference in means (illustrative)
def bootstrap_diff(a, b, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n):
        sa = rng.choice(a, size=len(a), replace=True)
        sb = rng.choice(b, size=len(b), replace=True)
        diffs.append(sa.mean() - sb.mean())
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return float(np.mean(diffs)), float(lo), float(hi)
```

If the design is broken (SRM, bad assignment, contaminated control), **stop** and report the design issue before any “winner.”

---

## Polars (large data)

```python
import polars as pl

lf = pl.scan_parquet("events/*.parquet")
result = (
    lf.filter(pl.col("ts") >= pl.datetime(2026, 1, 1))
      .group_by("country")
      .agg(
          pl.col("revenue_cents").sum().alias("revenue_cents"),
          pl.col("user_id").n_unique().alias("users"),
      )
      .with_columns(
          (pl.col("revenue_cents") / pl.col("users")).alias("rev_per_user")
      )
      .sort("revenue_cents", descending=True)
      .collect()
)
```

Push filters early; avoid collecting giant frames just to plot a summary.

---

## Gotchas (read when conclusions matter)

Before shipping a non-obvious insight, scan:

- Survivorship / only-success bias
- Simpson’s paradox (segment reverses aggregate)
- Changing denominators mid-series
- Timezone and late-arriving events
- Seasonality and day-of-week
- Double counting from join fan-out
- Leakage (using future data in a “predictive” feature)

Full list + mitigations: [references/gotchas.md](references/gotchas.md)

---

## Deliverables

| Ask | Deliver |
|-----|---------|
| Quick insight | 3–5 bullets + 1 chart + metric definition + n/date range |
| Stakeholder report | Markdown/PDF + PNG charts + assumptions/limitations |
| Reproducible | `.py` or notebook + cleaned parquet + seed if sampled |
| Experiment readout | Design summary, SRM check, primary + guardrails, effect + CI, decision |

### Report skeleton

```markdown
## Question
## Metric definitions
## Data (source, grain, range, filters, n)
## Findings (observation first, then interpretation)
## Charts
## Limitations & alternative explanations
## Recommended next check
```

Never present a chart without the question it answers.
Never present a rate without numerator and denominator.
