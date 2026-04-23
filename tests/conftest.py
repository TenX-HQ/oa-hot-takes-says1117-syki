"""Pytest fixtures for the Hot Takes Tournament assessment suite.

Each test gets a fresh temp SQLite database. DATABASE_URL is patched in
os.environ so the app's `get_connection` factory picks it up per call. The
TestClient is built after the patch so FastAPI's lifespan runs init_db
against the temp file.

Seed posts inserted by `init_db` are cleared before each test so tests can
assert on a known empty posts table — the tests seed their own data.
"""
import sqlite3

import pytest
from starlette.testclient import TestClient


def _patch_db(monkeypatch, db_path: str) -> None:
    monkeypatch.setenv("DATABASE_URL", db_path)


def _init_empty(db_path: str) -> None:
    from app.database import init_db

    # init_db seeds sample posts on an empty DB; run it once to materialize the
    # schema (lifespan will run it again but find posts already present and skip
    # reseeding) then clear seed rows for a known-empty starting state.
    init_db(db_path)


def _clear_seeds(db_path: str) -> None:
    """Clear seeded rows. Tolerant of a missing `matchups` table — a candidate
    who hasn't created it yet should still get a clean runner (tests then
    fail on their own assertions, not on fixture setup)."""
    conn = sqlite3.connect(db_path)
    try:
        try:
            conn.execute("DELETE FROM matchups")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("DELETE FROM posts")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient against an empty freshly-initialized SQLite DB."""
    db_path = str(tmp_path / "test.db")
    _patch_db(monkeypatch, db_path)
    _init_empty(db_path)
    from app.main import app

    with TestClient(app) as c:
        # Lifespan re-ran init_db against the seeded DB (no-op for seed).
        # Clear now so tests see an empty posts table.
        _clear_seeds(db_path)
        yield c


@pytest.fixture
def db_conn(tmp_path, monkeypatch):
    """Raw SQLite connection against the same temp DB the client uses.

    Lets tests insert posts / matchups directly with explicit timestamps so
    ordering assertions don't depend on wall-clock timing.
    """
    db_path = str(tmp_path / "test.db")
    _patch_db(monkeypatch, db_path)
    _init_empty(db_path)
    _clear_seeds(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture
def seeded_client(tmp_path, monkeypatch):
    """TestClient against a DB with the starter seed posts still present.

    Use for sentinel tests that confirm the GIVEN GET /posts anchor still
    returns the seeded foundation a candidate was given.
    """
    db_path = str(tmp_path / "test.db")
    _patch_db(monkeypatch, db_path)
    _init_empty(db_path)
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_with_db(tmp_path, monkeypatch):
    """Both a TestClient and a raw connection, sharing one temp DB.

    Use when a test needs to seed rows via raw SQL then hit the API.
    """
    db_path = str(tmp_path / "test.db")
    _patch_db(monkeypatch, db_path)
    _init_empty(db_path)
    from app.main import app

    with TestClient(app) as c:
        _clear_seeds(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield c, conn
        conn.close()
