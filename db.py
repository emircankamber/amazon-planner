import sqlite3

DB_NAME = "amazon_planner.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        email    TEXT    NOT NULL UNIQUE COLLATE NOCASE,
        hashed_pw TEXT   NOT NULL,
        created_at TEXT  DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ── Products ───────────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        sku            TEXT    NOT NULL,
        name           TEXT    DEFAULT '',
        lead_time_days INTEGER NOT NULL,
        z_value        REAL    NOT NULL,
        fba_stock      INTEGER NOT NULL DEFAULT 0,
        inbound_stock  INTEGER NOT NULL DEFAULT 0,
        updated_at     TEXT    DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, sku)
    );
    """)

    # ── Monthly Sales ──────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS monthly_sales (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        sku        TEXT    NOT NULL,
        year       INTEGER NOT NULL,
        month      INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
        units_sold INTEGER NOT NULL CHECK(units_sold >= 0),
        created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, sku, year, month)
    );
    """)

    conn.commit()
    conn.close()
