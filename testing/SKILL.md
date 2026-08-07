---
name: testing
description: >
  Write and improve automated tests: unit, integration, e2e. Covers pytest,
  Jest/Vitest, Go testing, fixtures, mocks vs fakes, property tests, snapshot
  discipline, and CI-friendly design. Use when adding tests, fixing flaky tests,
  raising coverage meaningfully, or designing a test plan.
---

# Testing

## Workflow

1. Inspect repository instructions, the existing test framework, neighboring tests, and the command used in CI.
2. Reproduce the behavior or failure before adding coverage when practical.
3. Test the public behavior at the lowest reliable layer; preserve project conventions and avoid unrelated production rewrites.
4. Run the narrowest relevant test first, then the broader affected suite.
5. Report exactly what ran, what passed, and what remains unverified.

## Philosophy

1. **Test behavior, not implementation** — assert outputs/effects users care about
2. **One reason to fail** per test when practical
3. **Deterministic** — no real clock, network, or unsorted maps without control
4. **Fast unit tests**; push slow stuff to integration layer
5. **Readable names** — `test_refund_fails_when_already_refunded`

Pyramid: many unit → fewer integration → few e2e.

---

## Pytest (Python)

```bash
pip install pytest pytest-asyncio pytest-cov
```

```python
import pytest
from app.billing import refund

def test_refund_full_amount():
    order = {"id": "o1", "total_cents": 1000, "status": "paid"}
    result = refund(order, amount_cents=1000)
    assert result["status"] == "refunded"
    assert result["refunded_cents"] == 1000

def test_refund_rejects_over_refund():
    order = {"id": "o1", "total_cents": 1000, "status": "paid"}
    with pytest.raises(ValueError, match="exceeds"):
        refund(order, amount_cents=1001)

@pytest.mark.parametrize("cents,ok", [(1, True), (0, False), (-5, False)])
def test_amount_validation(cents, ok):
    ...
```

### Fixtures

```python
@pytest.fixture
def db(tmp_path):
    # setup
    conn = connect(tmp_path / "t.db")
    yield conn
    conn.close()
```

### What to mock

| Mock | Don't mock |
|------|------------|
| External HTTP APIs | Your pure functions |
| Clock / random | In-memory domain logic |
| Cloud SDKs | Real DB in integration tests (often) |

Prefer **fakes** (in-memory repo) over heavy mocks.

More: [references/patterns.md](references/patterns.md)

---

## Jest / Vitest (JS/TS)

```ts
import { describe, it, expect, vi } from "vitest";
import { applyDiscount } from "./pricing";

describe("applyDiscount", () => {
  it("applies percent off", () => {
    expect(applyDiscount(1000, { type: "percent", value: 10 })).toBe(900);
  });

  it("never goes below zero", () => {
    expect(applyDiscount(50, { type: "fixed", value: 100 })).toBe(0);
  });
});
```

```ts
vi.useFakeTimers();
vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
// ...
vi.useRealTimers();
```

---

## Go

```go
func TestRefund_Full(t *testing.T) {
    t.Parallel()
    got, err := Refund(Order{TotalCents: 1000}, 1000)
    if err != nil {
        t.Fatal(err)
    }
    if got.Status != "refunded" {
        t.Fatalf("got %s", got.Status)
    }
}
```

Table-driven tests are idiomatic.

---

## Flaky test kill list

- Timezones / local clock
- Shared mutable global state
- Unordered maps/sets compared as lists
- Real network in unit tests or uncontrolled external services in integration tests
- Sleep-based synchronization — use conditions/signals
- Parallel tests touching same files/ports — isolate

---

## Coverage

- Aim coverage on **critical paths** (auth, billing, data loss)
- 100% global coverage is vanity; untested branches in money/PII code are not
- `pytest --cov=app --cov-report=term-missing`

---

## CI

```yaml
# sketch
- run: pytest -q
- run: npm test -- --run
```

Fail on flaky retries becoming habit — fix root cause.

---

## Anti-patterns

- Tests that only assert mock call order
- Snapshotting entire huge HTML blobs without review
- Sleep(1) to "wait for" async
- Testing private methods directly
- One 500-line test that sets up the universe
