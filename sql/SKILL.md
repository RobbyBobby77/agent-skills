---
name: sql
description: >
  Write, review, and optimize SQL in the dialect the database actually speaks:
  PostgreSQL, MySQL, SQLite, BigQuery, and Snowflake. Use for queries,
  migrations, indexes, EXPLAIN plans, window functions, CTEs, and modeling.
  Prefer data-analysis for interpreting result sets, csv for local files, xlsx
  for spreadsheet deliverables. Do not run writes or EXPLAIN ANALYZE on
  production data without explicit authorization.
---

# SQL

Agents write Postgres in a Snowflake warehouse, wrap indexed columns in
`DATE()`, and `EXPLAIN ANALYZE` a DELETE. This skill exists to stop that.

## Related skills

| Need | Skill |
|------|-------|
| Interpreting results, KPIs, charts | `data-analysis` |
| Local flat-file prep | `csv` |
| Spreadsheet deliverable | `xlsx` |
| Handler / contract in front of the query | `api` |

## Workflow

1. **Name the engine and version.** If you cannot, ask. Do not guess Postgres.
2. Inspect existing schema, migrations, naming, and whether execution is authorized.
3. Write parameterized SQL in that dialect. Qualify table assumptions.
4. Reads: bound the sample; inspect the plan when performance matters.
5. Writes/DDL: show affected objects, the transaction/rollback story, then run only when asked.

**Hard rules**
- Default to read-only analysis.
- Never interpolate user input into SQL. Bind values. Allowlist + quote identifiers.
- Never `EXPLAIN ANALYZE` mutating SQL, an unbounded `UPDATE`/`DELETE`, or production without authorization and a limit.
- Never put `CREATE INDEX CONCURRENTLY` inside a transaction.
- Unbounded `DELETE`/`UPDATE` is batched by key range, or it is not run.

---

## Dialect first

State the engine in the reply. Default examples below are **PostgreSQL**.

| Feature | Postgres | MySQL | SQLite | BigQuery | Snowflake |
|---------|----------|-------|--------|----------|-----------|
| Limit | `LIMIT n` | `LIMIT n` | `LIMIT n` | `LIMIT n` | `LIMIT n` |
| Upsert | `ON CONFLICT` | `ON DUPLICATE KEY` | `ON CONFLICT` | `MERGE` | `MERGE` |
| JSON | `jsonb` | `JSON_*` | `json_extract` | `JSON_*` | `VARIANT` / `:` path |
| Arrays | native | JSON arrays | limited | `ARRAY<>` | `ARRAY` |
| ILIKE | yes | `LIKE` + `LOWER` | `LIKE` | `LIKE` | `ILIKE` |
| Qualify windows | subquery | subquery | subquery | `QUALIFY` | `QUALIFY` |
| Bind style | `$1` | `%s` / `?` | `?` | `@param` / scripting | `%(name)s` / `?` |
| Identity | `GENERATED` / `serial` | `AUTO_INCREMENT` | `INTEGER PRIMARY KEY` | generate / `GENERATE_UUID` | sequences / UUID |
| Time now | `NOW()` | `NOW()` | `datetime('now')` | `CURRENT_TIMESTAMP()` | `CURRENT_TIMESTAMP()` |

Portable query recipes (dedupe, keyset, gaps-and-islands): [references/patterns.md](references/patterns.md).

### Engine landmines

**Postgres** — `COUNT(col)` ignores NULLs. `NOT IN (NULL-able subquery)` is empty; use `NOT EXISTS`. Partial indexes need the same predicate in the query. `CONCURRENTLY` cannot run in a transaction.

**MySQL** — `ONLY_FULL_GROUP_BY` rejects implicit groups. Identifier quotes are backticks. `utf8` is `utf8mb3`; prefer `utf8mb4`. `EXPLAIN ANALYZE` exists only on 8.0.18+.

**SQLite** — types are affinities, not constraints, unless `STRICT`. `ALTER TABLE` is limited (no drop column on old versions, no add constraint). One writer at a time.

**BigQuery** — you pay for bytes scanned. `SELECT *` is a cost bug. Partition + cluster; filter the partition column with a literal/range, not a wrapper. `QUALIFY` filters windows. No indexes to "add."

**Snowflake** — warehouse size drives both cost and time. `VARIANT` paths are `:foo` / `['foo']`, not `->`. `QUALIFY` and `MERGE` are first-class. Clustering is not a B-tree index. `INFORMATION_SCHEMA` views are billed; prefer `SHOW` / account usage for exploration. Time travel exists — do not treat `DELETE` as gone.

---

## Query style

```sql
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

1. Explicit columns — no `SELECT *` in production or BigQuery
2. Filter early; keep predicates sargable (`created_at >= $1`, not `DATE(created_at) = …`)
3. JOIN type is a decision. Accidental cross joins are defects
4. Parameters for values. Allowlisted quoted identifiers for table/column names
5. Aliases: `o` for orders is fine; `x` / `t1` is not
6. Know `COUNT(col)` vs `COUNT(*)`

---

## Windows, indexes, plans

```sql
SELECT user_id, amount_cents, created_at,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn,
  SUM(amount_cents) OVER (PARTITION BY user_id) AS user_total,
  LAG(created_at) OVER (PARTITION BY user_id ORDER BY created_at) AS prev_at
FROM orders;
```

```sql
-- Postgres: equality first, then range. Partial index matches the query predicate.
CREATE INDEX CONCURRENTLY idx_orders_user_created
  ON orders (user_id, created_at DESC)
  WHERE deleted_at IS NULL;
```

Snowflake/BigQuery: do not cargo-cult B-tree indexes. Partition/cluster instead.

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;   -- Postgres, authorized, non-mutating
```

Hunt: sequential scans on large tables, nested-loop explosions, rows removed by filter, on-disk sorts.

---

## Migrations

```sql
BEGIN;
ALTER TABLE users ADD COLUMN locale text;           -- nullable first
-- backfill in batches
-- ALTER TABLE users ALTER COLUMN locale SET NOT NULL;  -- later
COMMIT;
-- CREATE INDEX CONCURRENTLY ...  -- outside the transaction
```

- Expand/contract for zero-downtime (add nullable → backfill → constrain)
- Never rename and transform in one step without a rollback plan
- Store ordered files (`001_….sql`) matching the repo's migrator

---

## Anti-patterns

- `NOT IN (subquery with nulls)` — `NOT EXISTS`
- `OR` across different columns that kills the index — `UNION ALL` is sometimes the plan you want
- Functions or casts on the column side of a comparison
- Trusting client-side string concat
- Running a migration you have not shown

---

## Verify

```text
engine + version stated
binds used; no interpolated user input
read-only unless authorized
LIMIT / partition filter on expensive scans
writes: row estimate + rollback
```
