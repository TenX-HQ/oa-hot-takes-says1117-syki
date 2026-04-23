# TenX Assessment — do not modify this header
"""Seed script: populates posts and a few matchups for local development."""
import random
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.database import connection, init_db  # noqa: E402

SEED_POSTS = [
    "Pineapple belongs on pizza",
    "Tabs are strictly better than spaces",
    "Cold brew is overrated, hot coffee wins",
    "Every meeting should have been an email",
    "Dogs are objectively better than cats",
    "The best Star Wars movie is Empire Strikes Back",
    "Mechanical keyboards are worth the noise",
    "Dark mode is just better for your eyes",
]


def main() -> None:
    init_db()
    with connection() as conn:
        conn.execute("DELETE FROM matchups")
        conn.execute("DELETE FROM posts")
        ids: list[int] = []
        for content in SEED_POSTS:
            cur = conn.execute("INSERT INTO posts (content) VALUES (?)", (content,))
            ids.append(cur.lastrowid)
        rng = random.Random(42)
        for _ in range(40):
            a, b = rng.sample(ids, 2)
            conn.execute(
                "INSERT INTO matchups (winner_id, loser_id) VALUES (?, ?)", (a, b)
            )
    print(f"Seeded {len(SEED_POSTS)} posts and 40 matchups")


if __name__ == "__main__":
    main()
