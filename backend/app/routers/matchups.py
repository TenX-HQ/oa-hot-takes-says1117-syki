# TenX Assessment — do not modify this header
"""Endpoints for random matchup retrieval, vote recording, and ranked leaderboard."""
from fastapi import APIRouter, Query, status

from app.schemas import LeaderboardEntry, Matchup, VoteRequest, Post
from app.database import connection
from app import ranking

router = APIRouter(tags=["matchups"])


@router.get("/matchup")
def get_matchup() -> Matchup:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, content, created_at FROM posts ORDER BY RANDOM() LIMIT 2"
        ).fetchall()
    if len(rows) < 2:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not enough posts")
    return Matchup(
        post_a=Post(id=rows[0]["id"], content=rows[0]["content"], created_at=rows[0]["created_at"]),
        post_b=Post(id=rows[1]["id"], content=rows[1]["content"], created_at=rows[1]["created_at"])
    )


@router.post("/matchup/vote", status_code=status.HTTP_204_NO_CONTENT)
def record_vote(payload: VoteRequest):
    from fastapi import HTTPException

    if payload.winner_id == payload.loser_id:
        raise HTTPException(status_code=400, detail="Cannot vote for same post")

    with connection() as conn:
        # Verify both posts exist
        count = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE id IN (?, ?)",
            (payload.winner_id, payload.loser_id)
        ).fetchone()[0]
        if count != 2:
            raise HTTPException(status_code=400, detail="Invalid post IDs")

        conn.execute(
            "INSERT INTO matchups (winner_id, loser_id) VALUES (?, ?)",
            (payload.winner_id, payload.loser_id)
        )
    return None


@router.get("/leaderboard")
def get_leaderboard(sort: str = Query("best")) -> list[LeaderboardEntry]:
    from fastapi import HTTPException

    # region: leaderboard-dispatch
    sort_fn = {
        "recent": ranking.sort_recent,
        "best": ranking.sort_best,
        "hot": ranking.sort_hot,
        "controversial": ranking.sort_controversial,
    }.get(sort)

    if sort_fn is None:
        raise HTTPException(status_code=400, detail=f"Unknown sort: {sort}")
    # endregion: leaderboard-dispatch

    # region: leaderboard-aggregation
    with connection() as conn:
        rows = conn.execute("""
            SELECT
                p.id,
                p.content,
                p.created_at,
                SUM(CASE WHEN m.winner_id = p.id THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN m.loser_id = p.id THEN 1 ELSE 0 END) as losses,
                MAX(m.created_at) as last_matchup_at
            FROM posts p
            LEFT JOIN matchups m ON p.id = m.winner_id OR p.id = m.loser_id
            GROUP BY p.id
        """).fetchall()

    posts = [{
        "id": r["id"],
        "content": r["content"],
        "created_at": r["created_at"],
        "wins": r["wins"] or 0,
        "losses": r["losses"] or 0,
        "last_matchup_at": r["last_matchup_at"]
    } for r in rows]
    # endregion: leaderboard-aggregation

    sorted_posts = sort_fn(posts)
    for rank, post in enumerate(sorted_posts, start=1):
        post["rank"] = rank
        post["score"] = post.get("score", 0.0)

    return [LeaderboardEntry(**p) for p in sorted_posts]
