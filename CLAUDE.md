# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

ETL pipeline that extracts all raw tables from a MySQL source database (Basket Craft e-commerce) and loads them as-is into an AWS RDS PostgreSQL instance. No transformations — pure staging load.

## Running the Pipeline

```bash
python3 pipeline/extract.py
```

This reads all tables from MySQL and loads them into PostgreSQL. Each run drops and recreates every table (idempotent).

## Environment

Credentials live in `.env` (git-ignored). Required variables:

```
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DATABASE
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

## Architecture

`pipeline/extract.py` is the single script. It has three functions:
- `get_mysql_engine()` / `get_postgres_engine()` — build SQLAlchemy engines from `.env`
- `extract_and_load()` — discovers tables via `information_schema`, loops over them, reads each into a DataFrame, explicitly drops the destination table, then writes with `df.to_sql(..., if_exists="fail", method="multi")`

The explicit `DROP TABLE IF EXISTS ... CASCADE` before `to_sql` is intentional — it avoids a PostgreSQL composite type cache conflict that occurs when using `if_exists="replace"` on tables that were previously partially created.

## Dependencies

- `sqlalchemy`, `pandas`, `pymysql`, `psycopg2-binary`, `python-dotenv`
