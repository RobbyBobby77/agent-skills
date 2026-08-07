# SQL Patterns

## Deduplicate keep latest

```sql
SELECT DISTINCT ON (user_id) user_id, event_id, created_at, event_type
FROM events
ORDER BY user_id, created_at DESC;
-- portable:
SELECT user_id, event_id, created_at, event_type
FROM (
  SELECT user_id, event_id, created_at, event_type,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) rn
  FROM events
) t WHERE rn = 1;
```

## Upsert (Postgres)

```sql
INSERT INTO users (id, email, name)
VALUES ($1, $2, $3)
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name,
    updated_at = NOW();
```

## Gaps & islands (sessions)

```sql
-- flag new session if gap > 30 min
WITH ordered AS (
  SELECT user_id, ts,
    CASE WHEN ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) > INTERVAL '30 min'
         OR LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) IS NULL
    THEN 1 ELSE 0 END AS is_new
  FROM events
),
marked AS (
  SELECT *, SUM(is_new) OVER (PARTITION BY user_id ORDER BY ts) AS session_id
  FROM ordered
)
SELECT user_id, ts, session_id FROM marked;
```

## Running total

```sql
SELECT day, revenue,
  SUM(revenue) OVER (ORDER BY day) AS cumulative
FROM daily;
```

## Top-N per group

```sql
SELECT order_id, region, amount
FROM (
  SELECT order_id, region, amount,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rn
  FROM orders o
) t WHERE rn <= 3;
```

## Soft delete filter

```sql
WHERE deleted_at IS NULL
-- partial index:
-- CREATE INDEX ... ON t(col) WHERE deleted_at IS NULL;
```

## Pagination (keyset > OFFSET)

```sql
SELECT * FROM items
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```
