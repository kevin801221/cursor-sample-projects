import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.models import ProductPrice, PriceDropAlert

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pricebot.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            current_price REAL NOT NULL,
            lowest_price REAL NOT NULL,
            highest_price REAL NOT NULL,
            currency TEXT NOT NULL,
            in_stock INTEGER NOT NULL,
            url TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            price REAL NOT NULL,
            in_stock INTEGER NOT NULL,
            scraped_at TIMESTAMP NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    conn.commit()
    conn.close()

def save_price_record(item: ProductPrice) -> Optional[PriceDropAlert]:
    conn = get_connection()
    cursor = conn.cursor()
    now_str = item.scraped_at.strftime("%Y-%m-%d %H:%M:%S")

    # Check previous price
    cursor.execute("SELECT current_price, lowest_price, highest_price FROM products WHERE product_id = ?", (item.product_id,))
    row = cursor.fetchone()

    alert = None

    if row is None:
        # First time seeing product
        cursor.execute("""
            INSERT INTO products (product_id, title, current_price, lowest_price, highest_price, currency, in_stock, url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item.product_id, item.title, item.price, item.price, item.price, item.currency, 1 if item.in_stock else 0, item.url, now_str))
    else:
        old_price = row["current_price"]
        lowest = min(row["lowest_price"], item.price)
        highest = max(row["highest_price"], item.price)

        # Detect price drop (>= 5%)
        if old_price > item.price:
            drop_pct = round(((old_price - item.price) / old_price) * 100, 1)
            if drop_pct >= 5.0:
                alert = PriceDropAlert(
                    product_id=item.product_id,
                    title=item.title,
                    old_price=old_price,
                    new_price=item.price,
                    drop_percentage=drop_pct,
                    url=item.url,
                )

        cursor.execute("""
            UPDATE products
            SET title = ?, current_price = ?, lowest_price = ?, highest_price = ?, in_stock = ?, url = ?, updated_at = ?
            WHERE product_id = ?
        """, (item.title, item.price, lowest, highest, 1 if item.in_stock else 0, item.url, now_str, item.product_id))

    # Insert history log
    cursor.execute("""
        INSERT INTO price_history (product_id, price, in_stock, scraped_at)
        VALUES (?, ?, ?, ?)
    """, (item.product_id, item.price, 1 if item.in_stock else 0, now_str))

    conn.commit()
    conn.close()
    return alert

def get_all_products() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY updated_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_product_history(product_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM price_history WHERE product_id = ? ORDER BY scraped_at ASC", (product_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
