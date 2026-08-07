---
name: api
description: >
  Design, document, and implement HTTP APIs: REST, JSON, OpenAPI/Swagger,
  auth, pagination, errors, versioning, webhooks, and client usage. Use when
  building endpoints, writing OpenAPI specs, reviewing API contracts, or
  integrating third-party HTTP APIs.
---

# HTTP APIs

## Workflow

1. Inspect the existing routes, schemas, conventions, and authorization model before designing changes.
2. Confirm the API style, version, consumers, compatibility constraints, and source of truth.
3. Define the contract first: request, response, errors, auth, pagination, and idempotency.
4. Implement the smallest compatible change and add contract-focused tests.
5. Validate the OpenAPI document and exercise representative success and failure requests.

Preserve backward compatibility unless the user explicitly approves a breaking change. Never invent
third-party API details; inspect the supplied contract or current official documentation.

## Design checklist

| Concern | Prefer |
|---------|--------|
| Style | Resource-oriented REST unless RPC fits better |
| Format | JSON UTF-8; `Content-Type: application/json` |
| IDs | Opaque strings/UUIDs in URLs |
| Time | ISO-8601 UTC (`2026-03-15T12:00:00Z`) |
| Money | Integer minor units + currency code |
| Errors | Consistent problem body (below) |
| Versioning | URL `/v1` or explicit header — pick one, document it |
| Pagination | Cursor-based for large/changing sets; stable sort + limit + next_cursor |
| Auth | Bearer JWT/OAuth2/API key via header — never query string |
| Idempotency | `Idempotency-Key` on POSTs that create side effects |

---

## URL & methods

```
GET    /v1/orders              list
POST   /v1/orders              create
GET    /v1/orders/{id}         read
PATCH  /v1/orders/{id}         partial update
DELETE /v1/orders/{id}         delete (or cancel)
POST   /v1/orders/{id}/cancel  verb when state machine needs it
```

- Plural nouns; no verbs in path except deliberate actions
- Nest shallowly: `/v1/orders/{id}/items` OK; 3+ levels rarely

---

## Response shapes

### Success

```json
{
  "id": "ord_123",
  "status": "paid",
  "total_cents": 4200,
  "currency": "USD",
  "created_at": "2026-03-15T12:00:00Z"
}
```

### List + cursor

```json
{
  "data": [ { "id": "…" } ],
  "next_cursor": "eyJpZCI6…",
  "has_more": true
}
```

### Error (stable contract)

```json
{
  "error": {
    "code": "validation_error",
    "message": "amount_cents must be positive",
    "details": [
      { "field": "amount_cents", "issue": "must be > 0" }
    ],
    "request_id": "req_abc"
  }
}
```

Status codes: `400` validation, `401` unauth, `403` forbidden, `404` missing, `409` conflict, `422` semantic fail, `429` rate limit, `5xx` server.

---

## OpenAPI sketch

```yaml
openapi: 3.1.0
info:
  title: Orders API
  version: 1.0.0
paths:
  /v1/orders:
    get:
      summary: List orders
      parameters:
        - in: query
          name: cursor
          schema: { type: string }
        - in: query
          name: limit
          schema: { type: integer, minimum: 1, maximum: 100, default: 20 }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderList"
    post:
      summary: Create order
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OrderCreate"
      responses:
        "201":
          description: Created
components:
  schemas:
    OrderCreate:
      type: object
      required: [items]
      properties:
        items:
          type: array
          minItems: 1
          items:
            type: object
            required: [sku, qty]
            properties:
              sku: { type: string }
              qty: { type: integer, minimum: 1 }
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
security:
  - bearerAuth: []
```

More: [references/contracts.md](references/contracts.md)

---

## Client integration

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

Rules: timeouts always; retry only idempotent methods or with Idempotency-Key; respect `Retry-After`.

---

## Webhooks

- Sign payloads (HMAC header); verify before processing
- Verify against the exact raw request bytes before JSON parsing
- Deliver at-least-once → handlers **idempotent**
- Return 2xx quickly; async heavy work
- Provide event id + type + created_at

---

## Security

- Validate all input server-side
- Least-privilege scopes
- Rate limit by user/IP/key
- No sensitive data in URLs/logs
- CORS only for browser clients that need it
