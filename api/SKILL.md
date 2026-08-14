---
name: api
description: >
  Change, document, review, or integrate HTTP APIs without inventing a second
  contract: routes, OpenAPI/Swagger, auth, pagination, errors, versioning,
  webhooks, and client usage. Use when the task is an endpoint, a spec, a
  breaking-change review, or a third-party HTTP integration. Prefer json-yaml
  for spec file edits, testing for contract tests, sql for the query behind
  the handler. Do not use for GraphQL-only or gRPC-only work unless HTTP is
  also in scope.
---

# HTTP APIs

Greenfield taste is cheap. This skill exists because agents mint a new error
envelope next to the existing one, invent a third-party JSON shape from
memory, and ship a breaking rename as a "cleanup."

## Related skills

| Need | Skill |
|------|-------|
| Edit OpenAPI / JSON / YAML safely | `json-yaml` |
| Contract or handler tests | `testing` |
| Query / migration behind the handler | `sql` |
| Container or local dependency | `docker` |

## Workflow

1. **Inspect** existing routes, schemas, error bodies, auth, pagination, and the documented source of truth.
2. **Name the contract** you must match: this repo's API, or a third-party spec you have actually opened.
3. **Classify the change**: additive, breaking, or client-only. Breaking changes need explicit user approval.
4. **Implement the smallest compatible change** and add a contract test that would fail if the shape drifted.
5. **Exercise** one success and the relevant failure (401/403/404/409/422). Validate the spec if one exists.

**Hard rules**
- Never invent third-party fields, status codes, or auth schemes. Open the official contract or current docs.
- Never introduce a second pagination scheme, error envelope, time format, or ID type in the same API.
- Never break backward compatibility unless the user approves the exact break.
- Never put secrets or tokens in URLs, logs, or example fixtures that will be committed.
- Timeouts on every client call. Retry only idempotent methods, or POSTs that carry `Idempotency-Key`.

---

## Inspect the API you are in

Find the live convention before designing anything:

```bash
rg -n "next_cursor|page=|application/problem|error.:|Idempotency-Key|Authorization" \
  --glob '!node_modules' --glob '!.git'
rg -n "openapi:|swagger:" --glob '*.{yaml,yml,json}'
```

Record, even briefly:

```text
style:        REST | RPC-ish | mixed
source of truth: OpenAPI file | code | proto | none
auth:         bearer / API key header / cookie / mTLS
id type:      string ord_… / uuid / int
time:         RFC3339 UTC / unix / civil date
money:        integer minor units / decimal string / float (flag this)
errors:       {error:{code,message}} | RFC7807 | ad-hoc
pagination:   cursor | offset | none
versioning:   /v1 | header | none
idempotency:  header required on which methods
```

If those rows already have answers, your implementation copies them. The tables below are **only** for a greenfield API or an explicit redesign.

Compatibility, deprecation, PATCH, and idempotency store: [references/contracts.md](references/contracts.md).

---

## Greenfield defaults (only when nothing exists)

| Concern | Prefer |
|---------|--------|
| Style | Resource-oriented REST unless the operation is a true command |
| Format | JSON UTF-8; `Content-Type: application/json` |
| IDs | Opaque strings in URLs |
| Time | ISO-8601 UTC (`2026-03-15T12:00:00Z`) |
| Money | Integer minor units + currency code |
| Errors | One envelope, one `code` space, a `request_id` |
| Versioning | `/v1` **or** a version header — pick one and document it |
| Pagination | Cursor + stable sort + `limit` + `next_cursor` + `has_more` |
| Auth | Bearer / API key in a header — never the query string |
| Idempotency | `Idempotency-Key` on POSTs with side effects |

```
GET    /v1/orders
POST   /v1/orders
GET    /v1/orders/{id}
PATCH  /v1/orders/{id}
DELETE /v1/orders/{id}         # or POST …/cancel when delete is the wrong verb
POST   /v1/orders/{id}/cancel
```

Plural nouns. Nest one level (`/v1/orders/{id}/items`). No verbs in the path except deliberate actions.

```json
{
  "id": "ord_123",
  "status": "paid",
  "total_cents": 4200,
  "currency": "USD",
  "created_at": "2026-03-15T12:00:00Z"
}
```

```json
{ "data": [{ "id": "ord_123" }], "next_cursor": "eyJpZCI6…", "has_more": true }
```

```json
{
  "error": {
    "code": "validation_error",
    "message": "amount_cents must be positive",
    "details": [{ "field": "amount_cents", "issue": "must be > 0" }],
    "request_id": "req_abc"
  }
}
```

`400` validation, `401` unauth, `403` forbidden, `404` missing, `409` conflict, `422` semantic, `429` rate limit, `5xx` server.

---

## Third-party integrations

1. Open the supplier's current official docs or checked-in spec. Do not recall the shape.
2. Copy field names and auth verbatim. If two official pages disagree, say so and pick the one the live response matches.
3. Record base URL, versioning, pagination, rate limits, and idempotency in the client.
4. Contract-test against recorded fixtures (`testing` skill). Do not hit paid endpoints from unit tests.

---

## Clients

```bash
curl -sS -X POST "$BASE/v1/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"items":[{"sku":"SKU1","qty":2}]}'
```

```python
import httpx
r = httpx.post(
    f"{base}/v1/orders",
    headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
    json={"items": [{"sku": "SKU1", "qty": 2}]},
    timeout=30.0,
)
r.raise_for_status()
```

Respect `Retry-After`. Do not retry a bare POST that already may have created the resource.

---

## Webhooks

- Verify the signature against the **raw request bytes**, then parse JSON
- Treat delivery as at-least-once: handlers must be idempotent on event id
- Return 2xx quickly; do heavy work asynchronously
- Required fields: event id, type, created_at
- Reject unsigned or skew-expired payloads; do not process "to be helpful"

---

## Security

- Validate on the server. Never trust client-side checks.
- Least-privilege scopes. Rate-limit by principal, not just IP.
- No PII, tokens, or card data in URLs or default logs.
- CORS only for the browser origins that actually need it.

---

## Verify

| Change | Check |
|--------|-------|
| New/changed route | Success + the failure that is easy to get wrong (auth, 404, 409) |
| Spec edit | Parser + example request still valid |
| Client | Timeout set; retry policy matches idempotency |
| Breaking change | Compatibility notes in [references/contracts.md](references/contracts.md) and user approval recorded |

If you cannot send a real request, say which cases are untested.
