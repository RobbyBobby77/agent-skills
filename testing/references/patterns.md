# Testing patterns agents get wrong

## Characterization (legacy / unknown behavior)

When you do not know what the function should do, lock what it *does* today before changing it.

1. Call the function with the inputs from the bug or a representative fixture.
2. Assert the full observable output (return value, raised type, rows written).
3. Commit or at least keep that test.
4. Then change production code. The characterization test should fail if you alter behavior you did not mean to.

```python
def test_legacy_prorate_current_output():
    # recorded 2026-08-13 from production fixture invoice_8841
    assert prorate(cents=999, days_used=11, days_in_month=31) == 354
```

Do not "improve" the number while characterizing. If the number is wrong, add a second test named as the desired behavior and fix in a separate change.

## Snapshots

Allowed: a small, reviewed fixture (API JSON, rendered markdown, a single component).

Not allowed: an entire HTML document, minified bundle, or screenshot you did not inspect.

```text
1. Generate the snapshot
2. Read the whole file
3. Check for secrets, timestamps, absolute paths, leftover placeholders
4. Only then accept it
```

If the snapshot changes every run (time, id, path), the test is a flake — stabilize the input; do not keep regenerating.

## Contract tests

Own-API: assert status + body against the schema the `api` skill would treat as source of truth (OpenAPI, pydantic, zod). Use fixture payloads, not a live staging server, unless the user asked for a live check.

Third-party: replay recorded responses. Never hit a paid or rate-limited network from a unit test.

```python
def test_create_order_contract(client, order_schema):
    r = client.post("/v1/orders", json={"items": [{"sku": "A", "qty": 1}]})
    assert r.status_code == 201
    order_schema.validate(r.json())
```

## End-to-end

One journey per test. Seed isolated data. Never share a user with another test.

| Do | Don't |
|----|-------|
| Role/label/test-id selectors the product already uses | CSS-from-class-hash, `nth-child` |
| `expect(page.get_by_role("button", name="Pay")).to_be_visible()` | `sleep(3000)` then click |
| Seed via API / factory, then exercise the UI | Click through setup that is not under test |
| Assert the business outcome (order id on the page, row in DB) | Assert every CSS class on the way |

If the repo has Playwright, Cypress, or similar, use that. Do not add a second e2e runner.

Auth: reuse the project's test-login helper. Do not scrape a real SSO page in CI.

## Isolation

- Python: `tmp_path`, function-scoped fixtures, no leftover module globals
- JS: `beforeEach` local state; fake timers wrapped in try/finally (`useRealTimers`)
- Go: `t.Parallel()` only when there is no shared file/port; `t.TempDir()`; `-count=1` when debugging cache

```python
@pytest.fixture
def db(tmp_path):
    conn = connect(tmp_path / "t.db")
    yield conn
    conn.close()
```

## Factories over anonymous dicts

```python
def make_order(**overrides):
    base = {"id": "o1", "total_cents": 1000, "status": "paid", "currency": "USD"}
    return {**base, **overrides}
```

One builder per aggregate. Do not scatter `{"id": "o1", ...}` with slightly different keys.

## Property tests

Use when an invariant is cheaper to state than a list of cases (never-negative, encode/decode round-trip, sort is idempotent). Bound the input. A property that generates invalid domain objects is noise.

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=10_000))
def test_discount_never_negative(price):
    assert apply_discount(price, 100) >= 0
```

## What not to test

- Language/runtime features
- The ORM's `save()` unless you own a wrapper with extra rules
- Private helpers that only exist because you extracted them from one function
- Third-party SDK internals
