# SQL patterns (dialect-aware)

Default is Postgres. A second block is included when the portable form differs.

## Deduplicate, keep latest

```sql
-- Postgres
SELECT DISTINCT ON (user_id) user_id, event_id, created_at, event_type
FROM events
ORDER BY user_id, created_at DESC;
```

```sql
-- portable / BigQuery / Snowflake / MySQL 8
SELECT user_id, event_id, created_at, event_type
FROM (
  SELECT user_id, event_id, created_at, event_type,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM events
) t
WHERE rn = 1;
```

BigQuery/Snowflake can fold the filter: `… QUALIFY ROW_NUMBER() OVER (…) = 1`.

## Upsert

```sql
-- Postgres / SQLite
INSERT INTO users (id, email, name)
VALUES ($1, $2, $3)
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name,
    updated_at = NOW();
```

```sql
-- MySQL 8.0.20+ (VALUES(col) is deprecated)
INSERT INTO users (id, email, name)
VALUES (%s, %s, %s) AS new
ON DUPLICATE KEY UPDATE
  name = new.name,
  updated_at = NOW();
```

```sql
-- Snowflake
MERGE INTO users t
USING (SELECT %(id)s AS id, %(email)s AS email, %(name)s AS name) s
ON t.email = s.email
WHEN MATCHED THEN UPDATE SET name = s.name, updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (id, email, name) VALUES (s.id, s.email, s.name);
```

```sql
-- BigQuery
MERGE INTO users t
USING (SELECT @id AS id, @email AS email, @name AS name) s
ON t.email = s.email
WHEN MATCHED THEN UPDATE SET name = s.name, updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (id, email, name) VALUES (s.id, s.email, s.name);
```

## Keyset pagination (preferred over OFFSET)

```sql
SELECT id, created_at, title
FROM items
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

MySQL needs a comparable row constructor or an expanded `OR` form. Do not `OFFSET 100000`.

## Gaps and islands (sessions)

```sql
WITH ordered AS (
  SELECT user_id, ts,
    CASE
      WHEN ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) > INTERVAL '30 min'
        OR LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) IS NULL
      THEN 1 ELSE 0
    END AS is_new
  FROM events
),
marked AS (
  SELECT *, SUM(is_new) OVER (PARTITION BY user_id ORDER BY ts) AS session_id
  FROM ordered
)
SELECT user_id, ts, session_id FROM marked;
```

Snowflake interval math uses `DATEDIFF`; BigQuery uses `TIMESTAMP_DIFF`. Same idea.

## Top-N per group

```sql
SELECT order_id, region, amount
FROM (
  SELECT order_id, region, amount,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rn
  FROM orders
) t
WHERE rn <= 3;
```

## Soft delete

```sql
WHERE deleted_at IS NULL
-- Postgres partial index:
-- CREATE INDEX … ON t(col) WHERE deleted_at IS NULL;
```

Every query on that table needs the predicate, or the index will not match and deleted rows leak.

## Running total

```sql
SELECT day, revenue,
  SUM(revenue) OVER (ORDER BY day) AS cumulative
FROM daily;
```
