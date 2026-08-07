# Metric Definitions

Wrong metrics produce confident wrong decisions. Define first.

## Template

```text
Name:
Business question it answers:
Grain:              # row meaning: user-day, order, session, invoice-line
Entity:             # user | account | order | device | …
Formula:            # numerator / denominator or aggregation
Numerator:
Denominator:
Time window:        # rolling 7d, calendar month, cohort week
Timezone:
Population include:
Population exclude:
Status filters:     # paid only? exclude test? exclude refunded?
Source tables/files:
Owner / last reviewed:
Known caveats:
```

## Metric types

| Type | Example | Watch for |
|------|---------|-----------|
| Count | orders, signups | bots, duplicates, replays |
| Unique count | DAU/WAU/MAU | identity resolution, multi-device |
| Sum | revenue_cents | currency, refunds, tax/shipping inclusion |
| Ratio | conversion, CTR | unstable small denominators |
| Rate over time | retention D1/D7 | censoring for young cohorts |
| Distribution | p50/p95 latency | outliers, clock skew |
| Snapshot | ARR, seats | as-of timing, late corrections |

## KPI hygiene

1. **One primary metric per decision** — others are guardrails or diagnostics
2. **Money in minor units + currency** — never silent float dollars if precision matters
3. **Refunds / chargebacks** — decide gross vs net and stick to it
4. **Internal / test / employee** traffic — exclude with an explicit rule
5. **Identity** — user_id vs account_id vs device_id changes every unique metric
6. **Active definition** — “opened app” ≠ “meaningful action”; write the event name
7. **Version the definition** when it changes; don’t splice incompatible series without a break marker
8. **Document delayed data** — e.g. “complete after T+2 days”

## North-star vs diagnostics

- **North-star / primary**: what you optimize
- **Guardrails**: must not tank (error rate, refund rate, latency, complaints)
- **Diagnostics**: explain movement (funnel steps, segments) — not success criteria alone

## Ratios

Always pair:

```text
conversion = payers / starters
  payers   = users with paid event in window
  starters = users with start event in window
  note: starters from same cohort window, not all-time users
```

For rare events, show counts beside rates. A 50%→100% jump on n=2 is noise.

## Time windows

| Pattern | Use |
|---------|-----|
| Calendar month | Finance reporting |
| Rolling 7/28 day | Product trends, smooth DOW |
| Cohort-relative (D0, D7) | Retention, LTV |
| Session / unbounded | Avoid for KPIs unless defined |

Align comparisons: week vs week with same DOW mix when possible; flag holidays.

## Anti-patterns

- Vanity metrics that always go up with traffic (page views alone)
- Averaging percentages across unequal groups without weighting
- Blending currencies or tax-included/excluded revenue
- “Users” without saying registered vs anonymous vs billed seats
- Silent filter drift (“we always exclude mobile” not written down)
