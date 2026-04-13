import os
import sqlite3
from contextlib import contextmanager

import dotenv

dotenv.load_dotenv()

DB_PATH = os.getenv("DB_PATH", "/data/agent.db")  # Optional override for local testing


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        details TEXT DEFAULT 'none',
        due_date TEXT,
        reminder_cadence TEXT DEFAULT 'none',
        completed BOOLEAN DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_reminded_at TEXT
    )
    """)

    conn.commit()
    conn.close()


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
