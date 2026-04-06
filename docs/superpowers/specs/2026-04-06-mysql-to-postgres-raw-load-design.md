# Design: MySQL → PostgreSQL Raw Table Load

**Date:** 2026-04-06
**Status:** Approved

## Overview

Replace `pipeline/extract.py` with a script that extracts all raw tables from the Basket Craft MySQL source database and loads them as-is into the AWS RDS PostgreSQL destination. No transformations — pure staging load.

## Architecture

Single Python script: `pipeline/extract.py`

Three functions:
- `get_mysql_engine()` — builds MySQL SQLAlchemy engine from `.env` (`MYSQL_*` vars)
- `get_postgres_engine()` — builds PostgreSQL SQLAlchemy engine from `.env` (`RDS_*` vars)
- `extract_and_load()` — discovers all tables, loops over them, reads each into a DataFrame, writes to PostgreSQL

`__main__` block calls `extract_and_load()` directly.

## Data Flow

```
MySQL (MYSQL_HOST/PORT/USER/PASSWORD/DATABASE)
  → information_schema query → list of table names
  → pd.read_sql(table_name) → DataFrame (one table at a time)
  → df.to_sql(table_name, pg_engine, if_exists='replace', index=False, method='multi')
  → PostgreSQL RDS (RDS_HOST/PORT/USER/PASSWORD/DATABASE)
```

## Key Decisions

| Decision | Choice | Reason |
|---|---|---|
| Table discovery | `information_schema.tables` WHERE `table_schema = database_name` | Standard, no extra deps |
| On conflict | `if_exists='replace'` | Drop and recreate on each run — idempotent staging load |
| Index | `index=False` | Avoid writing pandas row index as a spurious column |
| Insert method | `method='multi'` | Faster bulk inserts vs row-by-row default |
| Chunking | None | Classroom-sized dataset fits in memory |

## Dependencies

Existing (already in use):
- `sqlalchemy`
- `pandas`
- `pymysql`
- `python-dotenv`

New:
- `psycopg2-binary` — PostgreSQL dialect driver for SQLAlchemy

## Environment Variables

Read from `.env`:

```
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DATABASE
```

## Success Criteria

- All tables in the MySQL `basket_craft` database are present in the PostgreSQL `basket_craft` database
- Row counts match between source and destination for each table
- Script prints per-table confirmation with row counts
- Script is idempotent (safe to run multiple times)
