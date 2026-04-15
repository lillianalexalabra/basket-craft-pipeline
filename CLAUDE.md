# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Two-step EL pipeline for the Basket Craft e-commerce dataset:

1. **Extract** — pulls all raw tables from a MySQL source database into AWS RDS PostgreSQL (no transformations, pure staging load)
2. **Load to Snowflake** — appends all raw tables from RDS PostgreSQL into Snowflake `basket_craft.raw`

## Running the Pipeline

**Step 1: MySQL → RDS PostgreSQL**
```bash
python3 pipeline/extract.py
```
Reads all tables from MySQL and loads them into PostgreSQL. Each run drops and recreates every table (idempotent).

**Step 2: RDS PostgreSQL → Snowflake**
```bash
python3 pipeline/load_snowflake.py
```
Reads all tables from RDS and appends them into Snowflake `basket_craft.raw`. Uses `write_pandas` for fast bulk loading via internal staging.

## Environment

Credentials live in `.env` (git-ignored). Required variables:

```
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DATABASE
SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA
```

## Databases

**MySQL source** (`MYSQL_*`):
- Host: `db.isba.co`, port 3306
- Database: `basket_craft`
- 8 tables: `employees`, `order_item_refunds`, `order_items`, `orders`, `products`, `users`, `website_pageviews`, `website_sessions`

**PostgreSQL destination** (`RDS_*`):
- AWS RDS instance: `basket-craft-db` (us-east-2)
- Endpoint: `basket-craft-db.cvwcia0igw9f.us-east-2.rds.amazonaws.com`, port 5432
- Database: `basket_craft`, user: `student`
- Instance class: `db.t3.micro` (free tier)

**Snowflake destination** (`SNOWFLAKE_*`):
- Database: `basket_craft`, schema: `raw`
- Account, user, password, and warehouse are in `.env`

## Architecture

**`pipeline/extract.py`** — MySQL → RDS:
- `get_mysql_engine()` / `get_postgres_engine()` — build SQLAlchemy engines from `.env`
- `extract_and_load()` — discovers tables via `information_schema`, loops over them, reads each into a DataFrame, explicitly drops the destination table, then writes with `df.to_sql(..., if_exists="fail", method="multi")`

The explicit `DROP TABLE IF EXISTS ... CASCADE` before `to_sql` is intentional — it avoids a PostgreSQL composite type cache conflict that occurs when using `if_exists="replace"` on tables that were previously partially created.

**`pipeline/load_snowflake.py`** — RDS → Snowflake:
- `get_postgres_engine()` — SQLAlchemy engine for RDS
- `get_snowflake_connection()` — native `snowflake.connector` connection from `.env`
- `load_to_snowflake()` — discovers tables in the RDS `public` schema, reads each into a DataFrame, appends to Snowflake using `write_pandas` with `auto_create_table=True` and `quote_identifiers=False`

## Dependencies

All dependencies are in `requirements.txt`. Install into the project virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- `sqlalchemy`, `pandas`, `pymysql`, `psycopg2-binary`, `python-dotenv` — used by both scripts
- `snowflake-connector-python[pandas]` — used by `load_snowflake.py`
