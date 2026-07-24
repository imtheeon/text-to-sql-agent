"""Claude Haiku-powered Text-to-SQL agent for the DuckDB analytics warehouse."""
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
import anthropic

from data.setup_db import get_connection

load_dotenv()

SYSTEM_PROMPT = """
You are an expert SQL analyst. Convert natural language questions into valid DuckDB SQL queries.

Database schema:

TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    name          VARCHAR,
    email         VARCHAR,
    region        VARCHAR,       -- North, South, East, West, Central
    tier          VARCHAR,       -- Bronze, Silver, Gold, Platinum
    signup_date   DATE,
    is_churned    BOOLEAN
)

TABLE products (
    product_id    INTEGER PRIMARY KEY,
    name          VARCHAR,
    category      VARCHAR,       -- Electronics, Furniture, Stationery
    unit_cost     DECIMAL(10,2),
    unit_price    DECIMAL(10,2)
)

TABLE marketing_campaigns (
    campaign_id   INTEGER PRIMARY KEY,
    name          VARCHAR,
    channel       VARCHAR,       -- Email, Social Media, Search, Display, Referral
    start_date    DATE,
    end_date      DATE,
    budget        DECIMAL(10,2),
    conversions   INTEGER
)

TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER,
    product_id    INTEGER,
    campaign_id   INTEGER,       -- nullable
    order_date    DATE,
    quantity      INTEGER,
    unit_price    DECIMAL(10,2),
    total_amount  DECIMAL(10,2), -- revenue = total_amount
    status        VARCHAR        -- completed, pending, processing, failed
)

Rules:
- Return ONLY the SQL query, no explanation, no markdown fences
- Never use DDL or DML (no CREATE, DROP, INSERT, UPDATE, DELETE)
- Limit results to 500 rows maximum
- revenue = total_amount; profit = total_amount - (unit_cost * quantity)
- For revenue metrics use only status = 'completed' orders unless asked otherwise
- Use DuckDB syntax (strftime, date_trunc, etc.)
"""


def generate_sql(question: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set. Add it to your .env file.")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}]
    )
    sql = message.content[0].text.strip()
    # Strip accidental markdown fences
    sql = re.sub(r"^```[\w]*\n?", "", sql)
    sql = re.sub(r"\n?```$", "", sql)
    return sql.strip()


def execute_query(sql: str) -> pd.DataFrame:
    con = get_connection(read_only=True)
    try:
        df = con.execute(sql).df()
    finally:
        con.close()
    return df


def ask(question: str) -> tuple[str, pd.DataFrame]:
    sql = generate_sql(question)
    df  = execute_query(sql)
    return sql, df
