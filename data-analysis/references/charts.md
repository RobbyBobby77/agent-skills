# Chart Recipes

## When to use which

| Question | Chart |
|----------|-------|
| Trend over time | Line (points if sparse) |
| Rank categories | Bar (sorted) |
| Part of whole (≤5 parts) | Stacked bar preferred over pie |
| Distribution | Histogram / KDE / box / violin |
| Relationship | Scatter (sample if huge) |
| Two-way intensity | Heatmap |
| Cohort retention | Heatmap (cohort × period) |
| Funnel | Horizontal bars or ordered cascade |
| Before/after or A/B | Paired bars + error bars / CI |

## Anatomy of a non-lying chart

1. Clear title that states the metric and window
2. Axis labels with units
3. Source / n / filters in caption or subtitle
4. Sorted categories when rank matters
5. Partial periods marked (e.g. “month in progress”)
6. Consistent colors for the same entities across figures

## Dual axis — avoid unless necessary

Dual axes mislead. Prefer:

- Indexed series (both start at 100)
- Two aligned panels sharing an x-axis
- Rate and volume as separate charts

## Annotation

```python
ax.axhline(goal, ls="--", color="gray", label="Goal")
ax.axvline(launch, ls=":", color="gray")
ax.annotate(
    "Launch",
    xy=(launch_x, launch_y),
    xytext=(10, 20),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="->"),
)
ax.legend(frameon=False)
```

## Cohort heatmap

```python
import seaborn as sns
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(
    retention_rates,
    annot=True,
    fmt=".0%",
    cmap="Blues",
    vmin=0,
    vmax=1,
    ax=ax,
)
ax.set_title("Monthly retention by signup cohort")
ax.set_xlabel("Months since signup")
ax.set_ylabel("Cohort")
fig.tight_layout()
fig.savefig("retention.png", dpi=150)
```

## Funnel

```python
import matplotlib.pyplot as plt

steps = ["view", "cart", "checkout", "paid"]
users = [10000, 4200, 1800, 900]
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(steps[::-1], users[::-1], color="#38bdf8")
for i, (s, u) in enumerate(zip(steps[::-1], users[::-1])):
    ax.text(u, i, f"  {u:,}", va="center")
ax.set_xlabel("Users")
ax.set_title("Checkout funnel (n at step)")
fig.tight_layout()
```

## Distribution with outliers

```python
# show both full and zoomed, or use log scale + note outliers
ax.hist(df["revenue_cents"].clip(upper=df["revenue_cents"].quantile(0.99)), bins=40)
ax.set_title("Revenue per order (clipped at p99 for display)")
```

Label when data is clipped — never clip the metric used in the headline number without saying so.

## A/B comparison

```python
# means with 95% CI whiskers if you have them
ax.bar(["control", "treatment"], [m0, m1], yerr=[e0, e1], capsize=4)
ax.set_ylabel("Conversion rate")
```

## Export for documents

| Target | Format |
|--------|--------|
| Slides / Word / PDF | PNG @ 150–200 dpi |
| Web docs | SVG or PNG |
| Interactive explore | Plotly HTML |

Always `tight_layout()` / constrained layout before save. Prefer colorblind-safe palettes (`sns.color_palette("colorblind")`).

## Anti-patterns

- 3D charts
- Rainbow pie with 10+ slices
- Smoothed curves on n < 20 without points
- Truncated bar axes
- Legend that doesn’t match series
- Screenshot of a spreadsheet as a “chart”
