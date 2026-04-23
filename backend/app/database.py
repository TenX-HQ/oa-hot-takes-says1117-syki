# TenX Assessment — do not modify this header
"""SQLite connection factory, schema DDL, and idempotent post seeding.

Owns connection lifecycle, foreign-key enforcement, schema bootstrap, and the
starter-post seed. No business logic, no query helpers — callers compose their
own SQL inside the `connection()` contextmanager.
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


def _resolve_path(db_path: str | None) -> str:
    if db_path is not None:
        return db_path
    return os.environ.get("DATABASE_URL", "app.db")


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Create a new SQLite connection with foreign keys enabled and Row factory set.

    PRAGMA foreign_keys is a per-connection setting in SQLite; it MUST be issued
    on every connection for the ON DELETE CASCADE / FK CHECK semantics to apply.
    """
    conn = sqlite3.connect(_resolve_path(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection(db_path: str | None = None) -> Iterator[sqlite3.Connection]:
    """Context-managed connection: commits on success, rolls back on error, always closes."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


DDL = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS matchups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    winner_id INTEGER NOT NULL REFERENCES posts(id),
    loser_id INTEGER NOT NULL REFERENCES posts(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (winner_id != loser_id)
);
"""


SEED_POSTS: list[str] = [
    "Pineapple belongs on pizza.",
    "Tabs are objectively better than spaces.",
    "The Oxford comma should be mandatory.",
    "Cereal is a soup.",
    "AI will make junior developers more valuable, not less.",
    "Dark mode is overrated.",
    "Every meeting should have a written agenda or be cancelled.",
    "Remote work is strictly better than hybrid.",
]


def seed_posts(conn: sqlite3.Connection) -> None:
    """Insert the 8 starter posts if the posts table is empty. Idempotent."""
    existing = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    if existing > 0:
        return
    conn.executemany(
        "INSERT INTO posts (content) VALUES (?)",
        [(p,) for p in SEED_POSTS],
    )
    conn.commit()


def init_db(db_path: str | None = None) -> None:
    """Initialize database schema and seed starter posts. Idempotent on every startup."""
    with connection(db_path) as conn:
        conn.executescript(DDL)
        seed_posts(conn)
