# Analysis Gotchas

Use this before shipping a surprising conclusion.

## Sampling & population

| Trap | What happens | Mitigation |
|------|--------------|------------|
| Survivorship | Only completers/winners in the data | Start from entry cohort; include churned |
| Selection bias | Sample ≠ population of interest | State inclusion rules; compare demo vs pop |
| Convenience export | One region/product only | Label scope; don’t generalize |
| Bot / QA traffic | Inflated actives, weird funnels | Filter known bots/internal; show with/without |

## Aggregation lies

| Trap | What happens | Mitigation |
|------|--------------|------------|
| Simpson’s paradox | Aggregate trend opposite of every segment | Segment by confounder (device, country, plan) |
| Average of ratios | Misleading blended % | Weighted by denominator or compute from totals |
| Join fan-out | Revenue double-counted after join | Validate row counts pre/post join; aggregate before join |
| Non-additive metrics | Unique users summed across days ≠ MAU | Never sum unique counts across overlapping windows |

## Time

| Trap | What happens | Mitigation |
|------|--------------|------------|
| Timezone mix | Day boundaries shift | Store UTC; report in one zone |
| Late-arriving events | Recent days look weak | Use T+N complete windows; mark partial days |
| Seasonality / DOW | MoM “drop” is weekend mix | Compare same DOW; use rolling or YoY |
| Censoring | Young users can’t have D30 yet | Only include cohorts with full maturity |
| DST / leap / month length | Unequal period length | Prefer per-day rates or equal-length windows |

## Metrics & measurement

| Trap | What happens | Mitigation |
|------|--------------|------------|
| Changing definition mid-series | Fake trend break | Version metrics; annotate chart |
| Denominator shift | Rate moves with coverage, not behavior | Plot num and den separately |
| Nulls treated as zero | Inflated activity / deflated rates | Explicit fill policy |
| Outlier-driven mean | One whale moves revenue | Show median/p95 and winsorized as secondary |
| Leakage | “Predictive” feature uses future | Time-split; features only as-of prediction time |

## Charts that mislead

- Truncated y-axis on bars exaggerating tiny gaps
- Dual axes implying false correlation
- Cumulative charts hiding a stalled present
- Pie charts with 12 slices
- Smooth lines on sparse data without showing points/n

## Checks before you publish

```text
[ ] Metric definition written (grain, num, den, filters, TZ)
[ ] Row grain unique keys verified
[ ] Join row-count sanity (no unexpected fan-out)
[ ] n and date range stated
[ ] Segment cuts don’t reverse the story unnoticed
[ ] Recent incomplete days labeled or excluded
[ ] Alternative explanation considered (pipeline bug vs real change)
[ ] Code path can reproduce every headline number
```

## Pipeline bugs that look like insights

- Deploy changed event names → funnel cliff
- Tracking blocked on one platform → “mobile died”
- Double-fire events → conversion > 100%
- Clock skew on clients → out-of-order sessions
- Partial backfill → historic spike

When a metric moves >~20% day-over-day without a known cause, **prefer “validate instrumentation” over “declare victory/failure.”**
