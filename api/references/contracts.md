# API Contract Patterns

## Partial update (PATCH)

JSON Merge Patch mindset: omit = leave unchanged; `null` may clear if documented.

```json
{ "status": "canceled", "note": null }
```

Prefer explicit PATCH schema over overloading PUT.

## Filtering

```
GET /v1/orders?status=paid&created_after=2026-01-01T00:00:00Z&sort=-created_at
```

Document allowed filter fields; reject unknown with 400.

## Sparse fieldsets (optional)

```
GET /v1/orders?fields=id,status,total_cents
```

## Bulk operations

```
POST /v1/orders/bulk
{ "ops": [ { "method": "create", "body": {…} } ] }
```

Return per-item results; HTTP 200 with mixed success or 207 if you support it — document clearly.

## Rate limit headers

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710500000
```

## Deprecation

```
Deprecation: true
Sunset: Fri, 1 Jan 2027 00:00:00 GMT
Link: <https://docs.example.com/migration>; rel="deprecation"
```

## Idempotency store

Key + request hash → response status/body for 24h. Same key + different body = 409.
