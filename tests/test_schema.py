"""Schema / DDL tests.

Assertions are shape-agnostic: any candidate implementation that creates a
`matchups` table with at least one FK into `posts(id)` passes, regardless of
whether they picked the denormalized `(winner_id, loser_id)` shape or the
normalized `(post_a_id, post_b_id, winner_id)` shape.
"""
from __future__ import annotations


def test_matchups_table_exists(db_conn):
    """A table named `matchups` exists and references posts(id) in its DDL."""
    cols = db_conn.execute("PRAGMA table_info('matchups')").fetchall()
    assert cols, "expected a `matchups` table to be created by init_db()"

    row = db_conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='matchups'"
    ).fetchone()
    assert row is not None, "matchups table missing from sqlite_master"
    ddl = row["sql"] or ""
    assert "REFERENCES posts" in ddl, (
        f"expected a foreign-key reference to posts(id) in matchups DDL, got: {ddl!r}"
    )


def test_posts_endpoint_returns_seeded_data(seeded_client):
    """Sentinel: the GIVEN GET /posts anchor still returns the starter seed data.

    Per INTAKE, `GET /posts` is the working foundation and `init_db()` seeds
    eight starter posts idempotently. A candidate who breaks either the route
    or the seeding has regressed the foundation.
    """
    resp = seeded_client.get("/posts")
    assert resp.status_code == 200, f"GET /posts failed: {resp.status_code} {resp.text}"
    posts = resp.json()
    assert isinstance(posts, list)
    assert len(posts) >= 1, "expected at least one seeded post from init_db()"
    for p in posts:
        assert "id" in p and "content" in p and "created_at" in p
