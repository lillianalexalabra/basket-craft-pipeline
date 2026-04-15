# Design: RDS PostgreSQL → Snowflake Raw Load

**Date:** 2026-04-14
**Status:** Approved

## Overview

New standalone script `pipeline/load_snowflake.py` that reads all raw tables from the AWS RDS PostgreSQL database and appends them into the Snowflake `basket_craft.raw` schema. Runs after `pipeline/extract.py` as the second step of the pipeline.

## Architecture

Single Python script: `pipeline/load_snowflake.py`

Three functions:
- `get_postgres_engine()` — builds RDS PostgreSQL SQLAlchemy engine from `.env` (`RDS_*` vars)
- `get_snowflake_engine()` — builds Snowflake SQLAlchemy engine from `.env` (`SNOWFLAKE_*` vars)
- `load_to_snowflake()` — discovers all tables in the RDS `public` schema via `information_schema`, reads each into a DataFrame, appends to Snowflake `basket_craft.raw`

`__main__` block calls `load_to_snowflake()` directly.

## Data Flow

```
RDS PostgreSQL (public schema)
  → information_schema query → list of table names
  → pd.read_sql(table) → DataFrame (one table at a time)
  → df.to_sql(table, snowflake_engine, if_exists="append", index=False, method="multi")
  → Snowflake basket_craft.raw
```

## Run Order

```bash
python3 pipeline/extract.py        # Step 1: MySQL → RDS PostgreSQL
python3 pipeline/load_snowflake.py # Step 2: RDS PostgreSQL → Snowflake
```

## Key Decisions

| Decision | Choice | Reason |
|---|---|---|
| Destination behavior | `if_exists="append"` | Accumulate data across runs |
| Table discovery | `information_schema.tables` WHERE `table_schema = 'public'` | Matches existing extract.py pattern |
| Index | `index=False` | Avoid writing pandas row index as a spurious column |
| Insert method | `method="multi"` | Faster bulk inserts vs row-by-row default |
| Chunking | None | Classroom-sized dataset fits in memory |
| Library | `snowflake-sqlalchemy` | Consistent with existing SQLAlchemy pattern in extract.py |

## Credentials

Read from `.env`:

```
SNOWFLAKE_ACCOUNT    # e.g. abc12345.us-east-1
SNOWFLAKE_USER       # Snowflake username
SNOWFLAKE_PASSWORD   # Snowflake password
SNOWFLAKE_WAREHOUSE  # e.g. COMPUTE_WH
SNOWFLAKE_DATABASE   # basket_craft
SNOWFLAKE_SCHEMA     # raw
```

Connection string format:
```
snowflake://<user>:<password>@<account>/<database>/<schema>?warehouse=<warehouse>
```

## Dependencies

Existing:
- `sqlalchemy`
- `pandas`
- `psycopg2-binary`
- `python-dotenv`

New:
- `snowflake-sqlalchemy` — Snowflake dialect for SQLAlchemy

## Output

Per-table confirmation with row count:

```
[load]    employees: 20 rows appended to basket_craft.raw
[load]    order_item_refunds: 1,731 rows appended to basket_craft.raw
[load]    order_items: 40,025 rows appended to basket_craft.raw
[load]    orders: 32,313 rows appended to basket_craft.raw
[load]    products: 4 rows appended to basket_craft.raw
[load]    users: 31,696 rows appended to basket_craft.raw
[load]    website_pageviews: 1,188,124 rows appended to basket_craft.raw
[load]    website_sessions: 472,871 rows appended to basket_craft.raw
[done]    All tables loaded to Snowflake basket_craft.raw.
```

## Success Criteria

- All 8 tables from RDS `public` schema are present in Snowflake `basket_craft.raw`
- Row counts in Snowflake match RDS source
- Script prints per-table confirmation with row counts
- Script runs cleanly after `extract.py` with no manual steps between them
