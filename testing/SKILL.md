---
name: testing
description: >
  Add, fix, and plan automated tests that match the repository's existing
  framework and CI command. Use for unit, integration, and end-to-end coverage,
  flake forensics, characterization of untested behavior, snapshot review, and
  test-plan design. Prefer api for contract shape; git-pr for running checks
  before a PR; docker for test containers. Do not use this skill to rewrite
  production code unless a test cannot be written otherwise.
---

# Testing

Agents already know "test behavior, not implementation." This skill exists
because they invent a second framework, mock the unit under test, sleep(1)
until CI is green, and raise coverage on getters while billing stays untested.

## Related skills

| Need | Skill |
|------|-------|
| HTTP contract / OpenAPI assertions | `api` |
| Commit, push, PR test plan | `git-pr` |
| Compose / service containers | `docker` |

## Workflow

1. **Inspect** the test runner, neighboring tests, fixtures, and the exact CI command before writing anything.
2. **Reproduce** the bug or name the behavior. If you cannot trigger it, you are not ready to assert it.
3. **Pick the lowest reliable layer** (table below). Match file layout, naming, and assertion style already in the tree.
4. **Run the narrowest command first**, then the affected suite. Do not add retries, sleeps, or `skip` to get green.
5. **Report** the exact command, pass/fail, and what remains unverified.

**Hard rules**
- Do not add pytest to a Jest repo, or a new e2e stack next to an existing one.
- Do not mock the unit you are testing. Fake the boundary behind it.
- Do not assert mock call order unless the call order is the product.
- Do not snapshot a huge blob you did not read.
- Do not change production code "to make it testable" without saying so and keeping the diff in scope.
- 100% coverage is not a goal. Untested auth, money, and deletion paths are.

---

## Inspect first

```bash
# runner + how CI invokes it
rg -n "pytest|vitest|jest|go test|playwright|cypress" .github/workflows .gitlab-ci.yml Makefile package.json pyproject.toml go.mod 2>/dev/null
# neighboring style
rg -n --glob '*test*' --glob '*_test.go' --glob '*.spec.*' -l . | head
```

Copy the repo's command. Typical shapes:

| Ecosystem | Narrow run | Broader run |
|-----------|------------|-------------|
| pytest | `pytest path/to/test_foo.py::test_name -q` | `pytest path/to -q` |
| Vitest / Jest | `npx vitest run path/to/foo.test.ts -t "name"` | `npm test -- --run` |
| Go | `go test ./pkg/billing -run TestRefund -count=1` | `go test ./... -count=1` |
| Playwright | `npx playwright test tests/checkout.spec.ts` | the CI script, unchanged |

If CI sets env vars, timezone, or seed flags, use those locally. A test that passes only on your machine is still broken.

---

## Choose a layer

| If the failure would be… | Write | Do not write |
|--------------------------|-------|--------------|
| Wrong return value, branch, or invariant in one module | Unit, with fakes at I/O | An e2e that clicks six pages |
| Wrong wiring between modules you own (HTTP handler + store) | Integration against the real adapter you can isolate | A mock of both sides |
| Wrong user-visible journey (auth cookie, checkout, upload) | One e2e path | A unit test of the page object |
| Unknown current behavior of a legacy function | Characterization test that locks today's output | A rewrite "while we're here" |
| A third-party HTTP contract | Contract test against fixtures / recorded payloads | Live calls in unit tests |

Pyramid still holds: many unit → fewer integration → few e2e. The table decides *this* test, not the repo's religion.

---

## What to assert

Name the test after the behavior: `test_refund_fails_when_already_refunded`.

Assert, in order of preference:

1. The user-visible result (status, returned value, stored row, HTTP code + body)
2. A single durable side effect (email queued, job enqueued)
3. Never: private method internals, mock call graphs, wall-clock, or "it didn't throw"

```python
def test_refund_rejects_over_refund(repo):
    order = repo.insert(total_cents=1000, status="paid")
    with pytest.raises(ValueError, match="exceeds"):
        refund(order, amount_cents=1001)
```

```ts
it("never goes below zero", () => {
  expect(applyDiscount(50, { type: "fixed", value: 100 })).toBe(0);
});
```

```go
func TestRefund_Full(t *testing.T) {
    t.Parallel()
    got, err := Refund(Order{TotalCents: 1000}, 1000)
    if err != nil {
        t.Fatal(err)
    }
    if got.Status != "refunded" {
        t.Fatalf("status=%s", got.Status)
    }
}
```

Control time, randomness, and clocks at the boundary. Prefer fakes (in-memory repo, fake mailer) over mocks. Patterns, characterization, snapshots, and e2e selectors: [references/patterns.md](references/patterns.md).

---

## Flakes are defects

A flake is a test that depends on something you did not control. Do not retry it in CI to hide that.

Procedure when a test is intermittent:

1. Run it in a loop until it fails locally. Stock pytest has no `--count`; Vitest has no `--repeat`. Keep `go test -count=20`.

   ```bash
   for i in $(seq 20); do pytest path/to/test_foo.py::test_name -q || break; done
   go test ./pkg/billing -run TestRefund -count=20
   for i in $(seq 20); do npx vitest run path/to/foo.test.ts -t "name" || break; done
   ```
2. Classify the dependency: clock, timezone, unordered collection, shared filesystem/port, real network, sleep, leaked global, test-order coupling.
3. Remove the dependency. Isolation beats `waitFor` timeouts; `waitFor` beats `sleep`.
4. Re-run the loop. If you cannot reproduce, say so — do not "fix" a flake you never saw fail.

| Smell | Fix |
|-------|-----|
| Local timezone / `datetime.now()` | Inject a clock; store UTC |
| `==` on a map/set iteration order | Compare as a set, or sort |
| Two tests bind `:8080` or write `./tmp` | `t.Parallel` + ephemeral port / `tmp_path` |
| `time.sleep(1)` / `await new Promise(r => setTimeout(r, 1000))` | Wait on a condition or fake the scheduler |
| Live Stripe / S3 / DNS in a unit test | Fake; record fixtures for contract tests |
| `retry: 3` in CI config | Forbidden as the fix |

---

## Coverage that matters

Instrument only to find untested *critical* branches:

```bash
pytest --cov=app --cov-report=term-missing
```

Read the missing list. Add a test for an untested refund path. Do not add a test that only exists to paint a line green.

---

## Report

```text
command: pytest tests/billing/test_refund.py -q
result: 4 passed
not run: e2e checkout (no browser in this environment)
still unverified: concurrent double-refund
```

If you could not run the suite the repo actually uses, that is a finding, not a footnote.
