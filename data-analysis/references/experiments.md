# Experiments & A/B Readouts

For agents assisting with experiment analysis — not a substitute for a stats platform.

## When this applies

- User mentions A/B, experiment, variant, treatment/control, feature flag split
- Two or more randomly assigned groups and a primary outcome

If assignment was **not** random (opt-in, rollout by region only, sales-selected), treat as observational — no “winner” language.

## Design checklist (read first)

1. **Unit of randomization** — user, account, session, pageview? Analysis unit should match (or use proper clustering)
2. **Assignment mechanism** — flag, edge hash, experiment service; sticky?
3. **Primary metric** — pre-declared; one is best
4. **Guardrails** — error rate, latency, refunds, support tickets, revenue
5. **Population** — who is eligible; exclusions
6. **Duration** — planned runtime vs actual; novelty window
7. **Interactions** — other concurrent experiments?

## Health checks (do these before uplift claims)

### Sample ratio mismatch (SRM)

```python
import numpy as np
from scipy.stats import chisquare

counts = df["variant"].value_counts().sort_index()
# expected equal split for 2 variants:
exp = [counts.sum() / len(counts)] * len(counts)
stat, p = chisquare(counts.values, f_exp=exp)
print(counts, "srm_p", p)
# p very small (e.g. < 0.001) → assignment/logging broken; do not trust results
```

### Contamination

- Users in multiple variants
- Cross-device identity splits
- Shared households / seats on account-randomized tests

```python
dup = df.groupby("user_id")["variant"].nunique()
print((dup > 1).mean(), "share of users in multiple variants")
```

### Balance (optional sanity)

Compare pre-period or covariates across variants; large imbalances suggest broken randomization or bots.

## Reporting template

```markdown
## Experiment
Name / ID:
Hypothesis:
Randomization unit:
Assignment:
## Data
Window (TZ):
Eligibility filters:
n control / n treatment:
SRM check:
## Primary metric
Definition:
Control mean (n):
Treatment mean (n):
Absolute diff:
Relative diff %:
Uncertainty (CI / test used):
## Guardrails
(metric: control → treatment, flag if worse)
## Decision
Ship / iterate / abort — and why
## Limitations
```

## Effect size > star gazing

Prefer:

- Absolute difference on the business scale (e.g. +0.4 pp conversion, +$0.03/user)
- Confidence interval or bootstrap interval
- Relative % only alongside absolute (10% of a tiny base is still tiny)

Avoid:

- Fishing across 30 metrics and reporting the one that “won”
- Peeking daily and stopping at first significant blip
- Declaring victory on p < 0.05 with no SRM/guardrail check

## Simple two-proportion sketch

```python
from statsmodels.stats.proportion import proportions_ztest

# successes, totals
count = np.array([treat_yes, ctrl_yes])
nobs = np.array([treat_n, ctrl_n])
stat, pval = proportions_ztest(count, nobs)
# still report rates and absolute lift
```

Use the project’s standard library/tooling when one exists (experimentation platform exports beat hand-rolled tests).

## Common failure modes

| Failure | Symptom |
|---------|---------|
| SRM | 48/52 becomes 40/60 without reason |
| Triggering bias | Metric only among users who saw UI that treatment changes |
| Novelty | Spike week 1, reverts week 2–3 |
| Network effects | Marketplace/social: units not independent |
| Underpowered | Huge CI; “not significant” ≠ “no effect” |
| Multiple comparisons | 20 metrics, one “wins” by chance |

## Decision language

**Good:** “Treatment conversion 4.2% (n=12,410) vs control 3.9% (n=12,388); +0.3 pp; 95% bootstrap CI [+0.05, +0.55]. SRM ok. Guardrails stable. Recommend ship.”

**Bad:** “Treatment won (p=0.04).”
