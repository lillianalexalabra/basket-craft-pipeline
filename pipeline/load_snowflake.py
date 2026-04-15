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
