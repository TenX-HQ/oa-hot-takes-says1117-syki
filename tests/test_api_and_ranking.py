"""Endpoint and ranking-algorithm tests.

Alternative-neutral: every test asserts the observable contract (status code,
response ordering, field presence) rather than a specific internal formula.
Any candidate ranking approach that addresses small-sample dominance — Laplace
smoothing, Wilson lower bound, Bayesian average, threshold-gated win rate —
passes the ranking tests.

Rejection-path tests (nonexistent / self-match) accept any 4xx or 5xx status
code. The assertion is "no bad row was inserted", not "the candidate picked
the reference error shape". Length-boundary tests likewise accept any 4xx
status (400 from a hand-rolled validator, 422 from Pydantic Field).
"""
from __future__ import annotations

import sqlite3
import time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OK_CREATED = (200, 201, 204)


def _create_post(client, content: str) -> int:
    r = client.post("/posts", json={"content": content})
    assert r.status_code in (200, 201), (
        f"failed to create post {content!r}: {r.status_code} {r.text}"
    )
    return r.json()["id"]


def _vote(client, winner_id: int, loser_id: int):
    return client.post(
        "/matchup/vote",
        json={"winner_id": winner_id, "loser_id": loser_id},
    )


def _assert_vote_ok(resp) -> None:
    assert resp.status_code in OK_CREATED, f"vote failed: {resp.status_code} {resp.text}"


def _leaderboard(client, sort: str | None = None) -> list[dict]:
    url = "/leaderboard" if sort is None else f"/leaderboard?sort={sort}"
    r = client.get(url)
    assert r.status_code == 200, f"GET {url} failed: {r.status_code} {r.text}"
    return r.json()


def _index_of(entries: list[dict], post_id: int) -> int:
    for i, e in enumerate(entries):
        if e["id"] == post_id:
            return i
    raise AssertionError(
        f"post id {post_id} not in leaderboard: {[e['id'] for e in entries]}"
    )


def _entry(entries: list[dict], post_id: int) -> dict:
    for e in entries:
        if e["id"] == post_id:
            return e
    raise AssertionError(
        f"post id {post_id} not in leaderboard: {[e['id'] for e in entries]}"
    )


def _count_matchups(conn: sqlite3.Connection) -> int:
    """Count matchups, returning 0 if the table doesn't exist yet.

    On a candidate branch without the matchups table, the rejection-path tests
    still assert the API returned 4xx/5xx; the row-count check trivially passes
    (0 before, 0 after) because no table means no inserts.
    """
    try:
        return conn.execute("SELECT COUNT(*) FROM matchups").fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def _seed_post(conn: sqlite3.Connection, content: str, created_at: str | None = None) -> int:
    if created_at is None:
        cur = conn.execute("INSERT INTO posts (content) VALUES (?)", (content,))
    else:
        cur = conn.execute(
            "INSERT INTO posts (content, created_at) VALUES (?, ?)",
            (content, created_at),
        )
    conn.commit()
    return cur.lastrowid


def _seed_vote(
    conn: sqlite3.Connection,
    winner_id: int,
    loser_id: int,
    created_at: str | None = None,
) -> None:
    if created_at is None:
        conn.execute(
            "INSERT INTO matchups (winner_id, loser_id) VALUES (?, ?)",
            (winner_id, loser_id),
        )
    else:
        conn.execute(
            "INSERT INTO matchups (winner_id, loser_id, created_at) VALUES (?, ?, ?)",
            (winner_id, loser_id, created_at),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Input validation — FR boundary
# ---------------------------------------------------------------------------

def test_post_creation_validates_length_boundaries(client):
    """POST /posts: 4 chars rejected, 5 chars accepted, 200 chars accepted, 201 chars rejected.

    Accepts any 4xx rejection status (400 hand-rolled, 422 Pydantic Field) —
    the assertion is that boundary behavior is correct, not that the error
    shape matches a specific style.
    """
    r = client.post("/posts", json={"content": "a" * 4})
    assert 400 <= r.status_code < 500, (
        f"4-char content should be rejected with 4xx, got {r.status_code}"
    )

    r = client.post("/posts", json={"content": "a" * 5})
    assert r.status_code in (200, 201), (
        f"5-char content should be accepted, got {r.status_code}: {r.text}"
    )

    r = client.post("/posts", json={"content": "a" * 200})
    assert r.status_code in (200, 201), (
        f"200-char content should be accepted, got {r.status_code}"
    )

    r = client.post("/posts", json={"content": "a" * 201})
    assert 400 <= r.status_code < 500, (
        f"201-char content should be rejected with 4xx, got {r.status_code}"
    )


# ---------------------------------------------------------------------------
# Vote integrity — M1.3
# ---------------------------------------------------------------------------

def test_vote_with_nonexistent_post_is_rejected(client_with_db):
    """POST /matchup/vote with an unknown post id must not insert a matchup row.

    Accepts any 4xx or 5xx status. The authoritative assertion is "no orphaned
    matchup row was inserted" — the enforcement layer is the candidate's call.
    """
    client, conn = client_with_db
    real_id = _create_post(client, "real post content here")

    before = _count_matchups(conn)
    r = _vote(client, real_id, 99999)
    assert r.status_code >= 400, (
        f"expected rejection for nonexistent loser, got {r.status_code}"
    )

    r = _vote(client, 99998, real_id)
    assert r.status_code >= 400, (
        f"expected rejection for nonexistent winner, got {r.status_code}"
    )

    after = _count_matchups(conn)
    assert after == before, (
        f"expected no matchup row inserted for invalid post ids, "
        f"but matchups grew from {before} to {after}"
    )


def test_vote_with_self_match_is_rejected(client_with_db):
    """POST /matchup/vote with winner_id == loser_id must not insert a row.

    Accepts any 4xx or 5xx status (400 app-layer guard, 500 surfacing a CHECK
    constraint violation).
    """
    client, conn = client_with_db
    pid = _create_post(client, "the only post in this test")

    before = _count_matchups(conn)
    r = _vote(client, pid, pid)
    assert r.status_code >= 400, f"expected rejection for self-match, got {r.status_code}"

    after = _count_matchups(conn)
    assert after == before, (
        f"expected no matchup row inserted for self-match, "
        f"but matchups grew from {before} to {after}"
    )


# ---------------------------------------------------------------------------
# Vote → leaderboard plumbing
# ---------------------------------------------------------------------------

def test_vote_records_winner_and_loser(client):
    """After one vote, the leaderboard shows winner w=1 and loser l=1."""
    a = _create_post(client, "post a first content")
    b = _create_post(client, "post b second content")

    _assert_vote_ok(_vote(client, a, b))

    entries = _leaderboard(client)
    ea = _entry(entries, a)
    eb = _entry(entries, b)
    assert ea["wins"] == 1, f"winner wins should be 1, got {ea}"
    assert ea["losses"] == 0, f"winner losses should be 0, got {ea}"
    assert eb["wins"] == 0, f"loser wins should be 0, got {eb}"
    assert eb["losses"] == 1, f"loser losses should be 1, got {eb}"


def test_leaderboard_response_shape(client):
    """Each entry exposes id, content, wins, losses, score, rank with correct types."""
    for c in ["alpha take content", "beta take content", "gamma take content"]:
        _create_post(client, c)

    entries = _leaderboard(client)
    assert isinstance(entries, list)
    assert len(entries) == 3, f"expected 3 entries, got {len(entries)}: {entries}"

    required_keys = {"id", "content", "wins", "losses", "score", "rank"}
    for e in entries:
        missing = required_keys - set(e.keys())
        assert not missing, f"leaderboard entry missing keys {missing}: {e}"
        assert isinstance(e["id"], int)
        assert isinstance(e["content"], str)
        assert isinstance(e["wins"], int)
        assert isinstance(e["losses"], int)
        assert isinstance(e["score"], (int, float)), (
            f"score must be numeric, got {type(e['score']).__name__}: {e['score']!r}"
        )
        assert isinstance(e["rank"], int)

    ranks = sorted(e["rank"] for e in entries)
    assert ranks == [1, 2, 3], f"ranks must be a 1..N sequence, got {ranks}"


# ---------------------------------------------------------------------------
# Ranking behavior
# ---------------------------------------------------------------------------

def test_leaderboard_recent_sorts_by_created_at(client_with_db):
    """`?sort=recent` returns posts ordered by created_at DESC (baseline)."""
    client, conn = client_with_db
    oldest = _seed_post(conn, "oldest take content", created_at="2024-01-01 00:00:00")
    middle = _seed_post(conn, "middle take content", created_at="2024-06-01 00:00:00")
    newest = _seed_post(conn, "newest take content", created_at="2025-01-01 00:00:00")

    entries = _leaderboard(client, sort="recent")
    order = [e["id"] for e in entries]
    assert order == [newest, middle, oldest], (
        f"expected recent sort to order newest→oldest, got {order}"
    )


def test_leaderboard_best_ranks_high_confidence_above_small_sample(client):
    """A 10W-2L post must rank above a 1W-0L post on `?sort=best`.

    Alternative-neutral: any small-sample correction (Wilson, Laplace,
    Bayesian, threshold) puts 10W-2L first. Naive wins/total fails this.
    """
    b = _create_post(client, "post b many matches content")
    c = _create_post(client, "post c filler opponent content")
    a = _create_post(client, "post a small sample content")

    _assert_vote_ok(_vote(client, a, c))  # A: 1W-0L
    for _ in range(10):
        _assert_vote_ok(_vote(client, b, c))  # B: 10W
    for _ in range(2):
        _assert_vote_ok(_vote(client, c, b))  # B: 10W-2L

    entries = _leaderboard(client, sort="best")
    idx_a = _index_of(entries, a)
    idx_b = _index_of(entries, b)
    assert idx_b < idx_a, (
        f"expected 10W-2L post (id={b}) to rank above 1W-0L post (id={a}) on best, "
        f"but got order {[e['id'] for e in entries]}"
    )


def test_leaderboard_controversial_ranks_high_volume_balanced_above_low_volume_balanced(client):
    """25W-24L ranks above 1W-1L on `?sort=controversial` — primary discriminator.

    Both posts have ~1.0 balance; only a formula that rewards volume places
    25W-24L first. Balance-alone fails this test.
    """
    # Four posts: two "contested" posts plus two filler opponents so we can
    # route wins/losses without entangling the contested posts with each other.
    hi_w = _create_post(client, "high volume winner content")
    hi_l = _create_post(client, "high volume loser content")
    lo_w = _create_post(client, "low volume winner content")
    lo_l = _create_post(client, "low volume loser content")

    # hi_w: 25W-24L; hi_l: 24W-25L (mirror)
    for _ in range(25):
        _assert_vote_ok(_vote(client, hi_w, hi_l))
    for _ in range(24):
        _assert_vote_ok(_vote(client, hi_l, hi_w))

    # lo_w: 1W-1L; lo_l: 1W-1L (mirror)
    _assert_vote_ok(_vote(client, lo_w, lo_l))
    _assert_vote_ok(_vote(client, lo_l, lo_w))

    entries = _leaderboard(client, sort="controversial")
    idx_hi = _index_of(entries, hi_w)
    idx_lo = _index_of(entries, lo_w)
    assert idx_hi < idx_lo, (
        f"expected 25W-24L post (id={hi_w}) to rank above 1W-1L post (id={lo_w}) "
        f"on controversial, but got order {[e['id'] for e in entries]} — "
        f"ranking formula fails to reward volume on top of balance"
    )


def test_leaderboard_hot_reflects_recent_matchups_not_post_age(client_with_db):
    """Older-but-recently-voted post ranks above newer-but-unvoted on `?sort=hot`.

    Catches candidates who decayed on posts.created_at instead of
    matchups.created_at. Uses direct DB seeding with explicit timestamps so
    the assertion does not depend on wall-clock timing.
    """
    client, conn = client_with_db

    # Old post + recent votes
    old_post = _seed_post(conn, "old post recently voted", created_at="2023-01-01 00:00:00")
    old_opp = _seed_post(conn, "old filler opponent content", created_at="2023-01-01 00:00:00")

    # New post, no votes
    new_post = _seed_post(conn, "new post never voted content", created_at="2025-01-01 00:00:00")

    # Recent matchup between old_post (wins) and old_opp
    recent_ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    for _ in range(3):
        _seed_vote(conn, old_post, old_opp, created_at=recent_ts)

    entries = _leaderboard(client, sort="hot")
    idx_old = _index_of(entries, old_post)
    idx_new = _index_of(entries, new_post)
    assert idx_old < idx_new, (
        f"expected older-but-recently-voted post (id={old_post}) to rank above "
        f"newer-but-unvoted post (id={new_post}) on hot, but got order "
        f"{[e['id'] for e in entries]} — hot must decay on matchups.created_at, "
        f"not posts.created_at"
    )


def test_leaderboard_rejects_unknown_sort(client):
    """`?sort=nonsense` returns 400 (not 500, not silent fallback)."""
    _create_post(client, "some content here")
    r = client.get("/leaderboard?sort=nonsense")
    assert r.status_code == 400, (
        f"expected 400 for unknown sort, got {r.status_code}: {r.text}"
    )


def test_matchup_never_pairs_post_with_itself(client):
    """Over 20 GET /matchup calls, post_a.id and post_b.id are always distinct."""
    _create_post(client, "first post for matchup test")
    _create_post(client, "second post for matchup test")

    for i in range(20):
        r = client.get("/matchup")
        assert r.status_code == 200, f"call {i}: {r.status_code} {r.text}"
        body = r.json()
        a = body["post_a"]["id"]
        b = body["post_b"]["id"]
        assert a != b, f"call {i}: matchup returned same post on both sides: {body}"


def test_leaderboard_default_sort_is_best(client):
    """`GET /leaderboard` with no sort param returns the same order as `?sort=best`."""
    a = _create_post(client, "post alpha content test")
    b = _create_post(client, "post beta content test")
    c = _create_post(client, "post gamma content test")

    # Seed uneven win distribution so best and recent diverge
    for _ in range(5):
        _assert_vote_ok(_vote(client, b, a))
    _assert_vote_ok(_vote(client, c, a))

    default_order = [e["id"] for e in _leaderboard(client)]
    best_order = [e["id"] for e in _leaderboard(client, sort="best")]
    assert default_order == best_order, (
        f"default leaderboard order must match ?sort=best; "
        f"default={default_order}, best={best_order}"
    )


def test_leaderboard_includes_zero_match_posts(client):
    """Posts with zero matches appear in the leaderboard alongside voted posts.

    After seeding three posts and casting a single vote on one pair, the
    unvoted post must still be present in GET /leaderboard?sort=best. Catches
    INNER-JOIN bugs that drop zero-match rows.
    """
    a = _create_post(client, "post a voted winner content")
    b = _create_post(client, "post b voted loser content")
    c = _create_post(client, "post c never voted content")

    _assert_vote_ok(_vote(client, a, b))

    entries = _leaderboard(client, sort="best")
    ids = {e["id"] for e in entries}
    assert {a, b, c} <= ids, (
        f"leaderboard dropped zero-match posts: expected all of "
        f"{{a={a}, b={b}, c={c}}} present, got {ids}"
    )

    ec = _entry(entries, c)
    assert ec["wins"] == 0 and ec["losses"] == 0, (
        f"zero-match post should show wins=0 losses=0, got {ec}"
    )
