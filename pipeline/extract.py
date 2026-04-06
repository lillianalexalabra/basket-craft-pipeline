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
            with pg_engine.begin() as pg_conn:
                pg_conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            df.to_sql(table, pg_engine, if_exists="fail", index=False, method="multi")
            print(f"[load]    {table}: {len(df):,} rows loaded")

    print("[done]    All tables loaded to PostgreSQL.")


if __name__ == "__main__":
    extract_and_load()
