# MySQL → PostgreSQL Raw Load Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `pipeline/extract.py` with a script that reads all raw tables from MySQL and loads them into PostgreSQL as-is.

**Architecture:** Discover all tables from MySQL's `information_schema`, loop over them reading each into a pandas DataFrame, and write each to PostgreSQL using `df.to_sql` with `if_exists='replace'`. Credentials loaded from `.env` via `python-dotenv`.

**Tech Stack:** Python 3, SQLAlchemy, pandas, pymysql, psycopg2-binary, python-dotenv

---

### Task 1: Rewrite `pipeline/extract.py`

**Files:**
- Modify: `pipeline/extract.py`

- [ ] **Step 1: Replace the file contents**

Write the following to `pipeline/extract.py`:

```python
"""
extract.py — Pull all raw tables from Basket Craft MySQL and load into PostgreSQL RDS.

Reads credentials from .env:
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
    RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DATABASE
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_mysql_engine():
    return create_engine(
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
        f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DATABASE']}"
    )


def get_postgres_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.environ['RDS_USER']}:{os.environ['RDS_PASSWORD']}"
        f"@{os.environ['RDS_HOST']}:{os.environ['RDS_PORT']}/{os.environ['RDS_DATABASE']}"
    )


def extract_and_load():
    mysql_engine = get_mysql_engine()
    pg_engine = get_postgres_engine()

    with mysql_engine.connect() as mysql_conn:
        tables = mysql_conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = :db ORDER BY table_name"
        ), {"db": os.environ["MYSQL_DATABASE"]}).fetchall()

    table_names = [row[0] for row in tables]
    print(f"[extract] Found {len(table_names)} tables: {', '.join(table_names)}")

    with mysql_engine.connect() as mysql_conn:
        for table in table_names:
            df = pd.read_sql(f"SELECT * FROM `{table}`", mysql_conn)
            df.to_sql(table, pg_engine, if_exists="replace", index=False, method="multi")
            print(f"[load]    {table}: {len(df):,} rows loaded")

    print("[done]    All tables loaded to PostgreSQL.")


if __name__ == "__main__":
    extract_and_load()
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/extract.py
git commit -m "Replace extract.py with full MySQL to PostgreSQL raw table load"
```

---

### Task 2: Run the pipeline

**Files:**
- Run: `pipeline/extract.py`

- [ ] **Step 1: Run the script**

```bash
python3 pipeline/extract.py
```

Expected output (table names and counts will vary):
```
[extract] Found N tables: orders, order_items, products, ...
[load]    order_items: X,XXX rows loaded
[load]    orders: X,XXX rows loaded
[load]    products: XX rows loaded
[done]    All tables loaded to PostgreSQL.
```

- [ ] **Step 2: Verify row counts in PostgreSQL**

```python
python3 -c "
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()

engine = create_engine(
    f'postgresql+psycopg2://{os.environ[\"RDS_USER\"]}:{os.environ[\"RDS_PASSWORD\"]}'
    f'@{os.environ[\"RDS_HOST\"]}:{os.environ[\"RDS_PORT\"]}/{os.environ[\"RDS_DATABASE\"]}'
)
with engine.connect() as conn:
    tables = conn.execute(text(
        \"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name\"
    )).fetchall()
    print(f'{'Table':<30} {'Rows':>10}')
    print('-' * 42)
    for (t,) in tables:
        n = conn.execute(text(f'SELECT COUNT(*) FROM \"{t}\"')).scalar()
        print(f'{t:<30} {n:>10,}')
"
```

Expected: each table present with matching row counts from MySQL.
