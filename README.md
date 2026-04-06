# Basket Craft Pipeline

ETL pipeline that extracts all raw tables from the Basket Craft MySQL source database and loads them into an AWS RDS PostgreSQL instance for analysis.

## Databases

| | MySQL (Source) | PostgreSQL (Destination) |
|---|---|---|
| Host | `db.isba.co` | `basket-craft-db.cvwcia0igw9f.us-east-2.rds.amazonaws.com` |
| Port | 3306 | 5432 |
| Database | `basket_craft` | `basket_craft` |
| User | `analyst` | `student` |

The PostgreSQL instance is an AWS RDS `db.t3.micro` in `us-east-2`.

## Tables Loaded

| Table | Rows |
|---|---:|
| employees | 20 |
| order_item_refunds | 1,731 |
| order_items | 40,025 |
| orders | 32,313 |
| products | 4 |
| users | 31,696 |
| website_pageviews | 1,188,124 |
| website_sessions | 472,871 |

## Setup

Copy `.env.example` to `.env` and fill in credentials (see CLAUDE.md for variable names).

Install dependencies:

```bash
pip3 install sqlalchemy pandas pymysql psycopg2-binary python-dotenv
```

## Running the Pipeline

```bash
python3 pipeline/extract.py
```

Each run drops and recreates all tables in PostgreSQL from the MySQL source (idempotent).
