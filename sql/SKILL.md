---
name: sql
description: >
  Write, review, and optimize SQL for PostgreSQL, MySQL, SQLite, BigQuery, and
  Snowflake-style dialects. Use for queries, migrations, indexes, EXPLAIN plans,
  window functions, CTEs, data modeling, and fixing slow or incorrect SQL. Prefer
  this over ad-hoc string building when the task is primarily database work.
---

# SQL

## Related skills

| Need | Skill |
|------|-------|
| Interpreting results, KPIs, charts, experiments | `data-analysis` |
| Local flat-file prep | `csv` |
| Spreadsheet deliverable | `xlsx` |

## Workflow

1. Identify the engine/version, schema, data volume, constraints, and whether execution is authorized.
2. Inspect existing migrations and query conventions; qualify assumptions about tables and cardinality.
3. Write parameterized SQL and validate syntax in the target dialect.
4. For reads, test on a bounded sample and inspect the plan when performance matters.
5. For writes or DDL, show affected rows/objects, transaction and rollback strategy, then execute only when requested.

Default to read-only analysis. Never run `EXPLAIN ANALYZE` on mutating SQL, an unbounded
`UPDATE`/`DELETE`, or production data without explicit authorization and safeguards.

## Dialect first

State the engine. Syntax differs for:

| Feature | Postgres | MySQL | SQLite | BigQuery |
|---------|----------|-------|--------|----------|
| Limit | `LIMIT n` | `LIMIT n` | `LIMIT n` | `LIMIT n` |
| Upsert | `ON CONFLICT` | `ON DUPLICATE KEY` | `ON CONFLICT` | `MERGE` |
| JSON | `jsonb` ops | `JSON_*` | `json_extract` | `JSON_*` |
| Arrays | native | JSON arrays | limited | `ARRAY<>` |
| ILIKE | yes | `LIKE` + lower | `LIKE` | `LIKE` |

Default examples below are **PostgreSQL** unless noted.

---

## Query style

```sql
-- Prefer CTEs for readable multi-step logic
WITH paid AS (
  SELECT user_id, SUM(amount_cents) AS revenue_cents
  FROM orders
  WHERE status = 'paid'
    AND created_at >= NOW() - INTERVAL '30 days'
  GROUP BY user_id
)
SELECT u.id, u.email, COALESCE(p.revenue_cents, 0) AS revenue_cents
FROM users u
LEFT JOIN paid p ON p.user_id = u.id
WHERE u.deleted_at IS NULL
ORDER BY revenue_cents DESC
LIMIT 100;
```

Rules:
1. **Explicit columns** — no `SELECT *` in production queries
2. **Filter early** — WHERE before heavy joins when possible
3. **sargable predicates** — don't wrap indexed cols: `created_at >= $1` not `DATE(created_at) = ...`
4. **JOIN types intentional** — INNER vs LEFT; never accidental cross join
5. **Parameters** — `$1` / `?` / named binds; never string-interpolate user input
6. **Aliases** short but clear (`o` for orders OK; `x`/`t1` not OK)
7. **NULLS** — know `COUNT(col)` vs `COUNT(*)`; use `COALESCE` for display
8. **Dynamic identifiers** — allowlist and quote them with the driver; bind parameters do not substitute table/column names

---

## Window functions

```sql
SELECT
  user_id,
  amount_cents,
  created_at,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn,
  SUM(amount_cents) OVER (PARTITION BY user_id) AS user_total,
  LAG(created_at) OVER (PARTITION BY user_id ORDER BY created_at) AS prev_at
FROM orders;
```

Common: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`/`LEAD`, `SUM/AVG() OVER`, `first_value`.

---

## Indexes (mental model)

```sql
-- Equality + range: put equality cols first
CREATE INDEX CONCURRENTLY idx_orders_user_created
  ON orders (user_id, created_at DESC)
  WHERE deleted_at IS NULL;  -- partial index
```

- Index columns used in `WHERE`, `JOIN`, `ORDER BY`
- Composite: leftmost prefix rule
- Covering / INCLUDE when selective queries fetch few extra cols
- Don't index low-cardinality alone (`boolean`) without reason

---

## EXPLAIN

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

Hunt for: Seq Scan on large tables, Nested Loop explosions, high rows removed by filter, sorts spilling to disk.

---

## Migrations mindset

```sql
BEGIN;
ALTER TABLE users ADD COLUMN locale text NOT NULL DEFAULT 'en';
-- backfill if needed
-- ADD CONSTRAINT / INDEX CONCURRENTLY outside long txn when required
COMMIT;
```

- Expand/contract for zero-downtime (add nullable → backfill → constrain)
- Never rename+transform in one scary step without rollback plan
- Store migrations as ordered files (`001_…sql`)

More: [references/patterns.md](references/patterns.md)

---

## Anti-patterns

- `NOT IN (subquery with nulls)` — use `NOT EXISTS`
- `OR` across columns that kills indexes — `UNION ALL` sometimes better
- Functions on column side of compare
- Implicit type casts that prevent index use
- Unbounded `DELETE`/`UPDATE` — batch with key ranges
- Trusting client-side string SQL concat

---

## SQLite notes

- `INTEGER PRIMARY KEY` is rowid alias
- Limited `ALTER TABLE`
- Good for local/dev; careful with concurrent writes

## BigQuery notes

- Partition + cluster for cost
- Avoid `SELECT *` (bytes billed)
- `QUALIFY` for window filters
