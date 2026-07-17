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
    CREATE TABLE IF NOT EXISTS agent_jobs (
        id           TEXT PRIMARY KEY,
        instruction  TEXT NOT NULL,
        status       TEXT NOT NULL DEFAULT 'pending',
        scheduled_at TEXT NOT NULL,
        recurrence   TEXT,
        notify_via   TEXT NOT NULL DEFAULT '["telegram"]',
        last_run_at  TEXT,
        result       TEXT,
        error        TEXT,
        created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT NOT NULL,
        description  TEXT,
        status       TEXT NOT NULL DEFAULT 'pending',
        priority     TEXT,
        due_date     TEXT,
        scheduled_at TEXT,
        recurrence   TEXT,
        notify_via   TEXT,
        created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
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
