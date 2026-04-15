# RDS PostgreSQL → Snowflake Raw Load Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `pipeline/load_snowflake.py` that reads all raw tables from RDS PostgreSQL and appends them into the Snowflake `basket_craft.raw` schema using `snowflake-connector-python`'s `write_pandas`.

**Architecture:** Discover all tables in the RDS `public` schema via `information_schema`, read each into a pandas DataFrame using SQLAlchemy, and append to Snowflake using `write_pandas` with `auto_create_table=True` and `quote_identifiers=False`. Credentials are read from `.env` via `python-dotenv`.

**Tech Stack:** Python 3, SQLAlchemy, pandas, psycopg2-binary, snowflake-connector-python[pandas], python-dotenv

---

### Task 1: Create `requirements.txt`

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Write `requirements.txt`**

Create `/Users/alexalabra/isba-4715/basket-craft-pipeline/requirements.txt` with these exact contents:

```
sqlalchemy
pandas
pymysql
psycopg2-binary
python-dotenv
snowflake-connector-python[pandas]
```

- [ ] **Step 2: Install dependencies**

```bash
pip3 install -r requirements.txt
```

Expected: all packages install without error. `snowflake-connector-python[pandas]` may take a minute — it's a large package.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "Add requirements.txt with snowflake-connector-python dependency"
```

---

### Task 2: Create `pipeline/load_snowflake.py`

**Files:**
- Create: `pipeline/load_snowflake.py`

- [ ] **Step 1: Write the script**

Create `/Users/alexalabra/isba-4715/basket-craft-pipeline/pipeline/load_snowflake.py` with these exact contents:

```python
"""
load_snowflake.py — Load raw tables from RDS PostgreSQL into Snowflake basket_craft.raw.

Run after extract.py:
    python3 pipeline/extract.py        # MySQL → RDS
    python3 pipeline/load_snowflake.py # RDS → Snowflake

Reads credentials from .env:
    RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DATABASE
    SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
    SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA
"""

import os
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_postgres_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.environ['RDS_USER']}:{os.environ['RDS_PASSWORD']}"
        f"@{os.environ['RDS_HOST']}:{os.environ['RDS_PORT']}/{os.environ['RDS_DATABASE']}"
    )


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
        database=os.environ['SNOWFLAKE_DATABASE'],
        schema=os.environ['SNOWFLAKE_SCHEMA'],
    )


def load_to_snowflake():
    pg_engine = get_postgres_engine()
    sf_conn = get_snowflake_connection()

    with pg_engine.connect() as pg_conn:
        tables = pg_conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )).fetchall()

    table_names = [row[0] for row in tables]
    print(f"[load]    Found {len(table_names)} tables: {', '.join(table_names)}")

    database = os.environ['SNOWFLAKE_DATABASE']
    schema = os.environ['SNOWFLAKE_SCHEMA']

    with pg_engine.connect() as pg_conn:
        for table in table_names:
            df = pd.read_sql(f'SELECT * FROM "{table}"', pg_conn)
            df.columns = [col.upper() for col in df.columns]
            write_pandas(
                conn=sf_conn,
                df=df,
                table_name=table.upper(),
                database=database,
                schema=schema,
                auto_create_table=True,
                overwrite=False,
                quote_identifiers=False,
            )
            print(f"[load]    {table}: {len(df):,} rows appended to {database}.{schema}")

    sf_conn.close()
    print(f"[done]    All tables loaded to Snowflake {database}.{schema}.")


if __name__ == "__main__":
    load_to_snowflake()
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/load_snowflake.py
git commit -m "Add RDS to Snowflake raw load script"
```

---

### Task 3: Run and verify

**Files:**
- Run: `pipeline/load_snowflake.py`

- [ ] **Step 1: Run the script**

```bash
python3 pipeline/load_snowflake.py
```

Expected output:
```
[load]    Found 8 tables: employees, order_item_refunds, order_items, orders, products, users, website_pageviews, website_sessions
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

- [ ] **Step 2: Verify row counts in Snowflake**

In the Snowflake web UI or a Snowflake SQL client, run:

```sql
select table_name, row_count
from basket_craft.information_schema.tables
where table_schema = 'RAW'
order by table_name;
```

Expected: all 8 tables present with row counts matching the output above.
