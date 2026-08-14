# Compatibility and contract mechanics

Use this when the API already has clients, or when you are about to change a field.

## Is this breaking?

| Change | Class | Ship as |
|--------|-------|---------|
| Add optional request field | Additive | Same version |
| Add response field | Additive | Same version (clients must ignore unknowns) |
| Add endpoint | Additive | Same version |
| Widen a union / add enum value | Usually additive | Same version; document consumers that exhaustiveness-check |
| Make a required field optional | Additive | Same version |
| Rename field, remove field, change type | **Breaking** | New version or approved flag day |
| Change error envelope or pagination keys | **Breaking** | New version |
| Reuse a status code for a new meaning | **Breaking** | Don't |
| Change default page size or sort | Often breaking in practice | Treat as breaking if any client paginates |
| Make an optional field required | **Breaking** | New version |
| Change ID format or time format | **Breaking** | New version |

Do not "clean up" a public field name. Add the new field, deprecate the old one, keep both until the sunset date.

## Deprecation

```
Deprecation: true
Sunset: Fri, 1 Jan 2027 00:00:00 GMT
Link: <https://docs.example.com/migration>; rel="deprecation"
```

Document: what still works, the replacement, the sunset date, and how to tell a request is using the old path. Do not remove the old path in the same change that adds the header.

## PATCH

Match the repo. If none exists:

- Explicit PATCH schema. Omitted field = unchanged. `null` clears only if documented.
- Do not overload PUT to mean PATCH.

```json
{ "status": "canceled", "note": null }
```

## Pagination

Whatever the inspect step found, keep it. If you must add pagination to an unpaginated list, that is a behavior change for clients that assumed one page — call it out.

Cursor rules when you are the one introducing it:

- Opaque cursor, not a leaked offset
- Stable sort key, unique tie-breaker (`created_at, id`)
- `limit` max + default documented
- `next_cursor` absent or null when `has_more` is false

Offset/`page=` is acceptable only when the collection is already offset-paginated.

## Idempotency store

```
key + hash(request body) → {status, body}  for a documented TTL (often 24h)
same key + different body → 409
unknown key → execute, then store
```

Replay must return the original status and body, not a fresh 201 with a new id.

## Filters

```
GET /v1/orders?status=paid&created_after=2026-01-15T00:00:00Z&sort=-created_at
```

Allowlist filter fields. Unknown filters → `400`, not silent ignore (unless the existing API already ignores them — then match that).

## Rate limit headers

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1765900000
```

If the API already uses RFC 9239 `RateLimit-*` or a vendor prefix, keep it. Do not add a second family of headers.

## Review checklist

```text
[ ] Existing envelope / pagination / auth unchanged unless approved
[ ] Additive vs breaking classified
[ ] Example request works; example error is the real envelope
[ ] Idempotent methods stay idempotent; creating POSTs have a key or are documented as not
[ ] Webhook signature still covers the raw body
[ ] OpenAPI (if present) still parses and matches the handler
[ ] Contract test added or updated
```
