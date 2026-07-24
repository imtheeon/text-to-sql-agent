"""Create and seed the local DuckDB analytics warehouse."""
from pathlib import Path
import duckdb
import random
from datetime import date, timedelta

DB_PATH = Path(__file__).parent / "analytics.duckdb"


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def setup_database(force: bool = False) -> None:
    if DB_PATH.exists() and not force:
        return

    con = get_connection()

    con.execute("""
        CREATE OR REPLACE TABLE customers (
            customer_id   INTEGER PRIMARY KEY,
            name          VARCHAR,
            email         VARCHAR,
            region        VARCHAR,
            tier          VARCHAR,
            signup_date   DATE,
            is_churned    BOOLEAN
        )
    """)

    con.execute("""
        CREATE OR REPLACE TABLE products (
            product_id    INTEGER PRIMARY KEY,
            name          VARCHAR,
            category      VARCHAR,
            unit_cost     DECIMAL(10,2),
            unit_price    DECIMAL(10,2)
        )
    """)

    con.execute("""
        CREATE OR REPLACE TABLE marketing_campaigns (
            campaign_id   INTEGER PRIMARY KEY,
            name          VARCHAR,
            channel       VARCHAR,
            start_date    DATE,
            end_date      DATE,
            budget        DECIMAL(10,2),
            conversions   INTEGER
        )
    """)

    con.execute("""
        CREATE OR REPLACE TABLE orders (
            order_id      INTEGER PRIMARY KEY,
            customer_id   INTEGER REFERENCES customers(customer_id),
            product_id    INTEGER REFERENCES products(product_id),
            campaign_id   INTEGER,
            order_date    DATE,
            quantity      INTEGER,
            unit_price    DECIMAL(10,2),
            total_amount  DECIMAL(10,2),
            status        VARCHAR
        )
    """)

    # --- seed data ---
    random.seed(42)
    regions = ["North", "South", "East", "West", "Central"]
    tiers   = ["Bronze", "Silver", "Gold", "Platinum"]

    customers = []
    for i in range(1, 501):
        signup = date(2022, 1, 1) + timedelta(days=random.randint(0, 730))
        customers.append((
            i, f"Customer {i}", f"customer{i}@example.com",
            random.choice(regions), random.choice(tiers),
            signup, random.random() < 0.15
        ))
    con.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?)", customers)

    product_data = [
        (1, "Laptop Pro",      "Electronics",  800.00, 1299.99),
        (2, "Wireless Mouse",  "Electronics",    8.00,   29.99),
        (3, "Standing Desk",   "Furniture",    200.00,  499.99),
        (4, "Office Chair",    "Furniture",    150.00,  349.99),
        (5, "Notebook Pack",   "Stationery",     3.00,   12.99),
        (6, "Pen Set",         "Stationery",     2.00,    9.99),
        (7, "Headphones",      "Electronics",   60.00,  149.99),
        (8, "Webcam HD",       "Electronics",   35.00,   89.99),
        (9, "Desk Lamp",       "Furniture",     20.00,   54.99),
        (10,"Keyboard Mech",   "Electronics",   45.00,  119.99),
    ]
    con.executemany("INSERT INTO products VALUES (?,?,?,?,?)", product_data)

    channels = ["Email", "Social Media", "Search", "Display", "Referral"]
    campaigns = []
    for i in range(1, 21):
        start = date(2023, 1, 1) + timedelta(days=random.randint(0, 300))
        campaigns.append((
            i, f"Campaign {i}", random.choice(channels),
            start, start + timedelta(days=random.randint(14, 60)),
            round(random.uniform(1000, 20000), 2),
            random.randint(50, 500)
        ))
    con.executemany("INSERT INTO marketing_campaigns VALUES (?,?,?,?,?,?,?)", campaigns)

    price_map = {p[0]: p[4] for p in product_data}
    cost_map  = {p[0]: p[3] for p in product_data}
    statuses  = ["completed"] * 7 + ["pending", "processing", "failed"]
    orders = []
    for i in range(1, 2001):
        cid = random.randint(1, 500)
        pid = random.randint(1, 10)
        qty = random.randint(1, 5)
        price = price_map[pid]
        orders.append((
            i, cid, pid,
            random.randint(1, 20) if random.random() < 0.7 else None,
            date(2023, 1, 1) + timedelta(days=random.randint(0, 365)),
            qty, price, round(price * qty, 2),
            random.choice(statuses)
        ))
    con.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)", orders)

    con.close()
    print(f"Database seeded at {DB_PATH}")


if __name__ == "__main__":
    setup_database(force=True)
