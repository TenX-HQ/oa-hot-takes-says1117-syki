# TenX Assessment — do not modify this header
"""Ranking algorithms over pre-aggregated post dicts."""
from datetime import datetime


def sort_recent(posts: list[dict]) -> list[dict]:
    return sorted(posts, key=lambda p: p["created_at"], reverse=True)


def sort_best(posts: list[dict]) -> list[dict]:
    for p in posts:
        # Laplace smoothing: add 1 pseudo-win, 1 pseudo-loss
        p["score"] = (p["wins"] + 1) / (p["wins"] + p["losses"] + 2)
    return sorted(posts, key=lambda p: p["score"], reverse=True)


def sort_hot(posts: list[dict]) -> list[dict]:
    now = datetime.utcnow()
    for p in posts:
        total = p["wins"] + p["losses"]
        if total == 0:
            p["score"] = 0.0
            continue

        win_rate = p["wins"] / total

        # Decay on last matchup time
        if p["last_matchup_at"]:
            last = datetime.fromisoformat(p["last_matchup_at"])
            hours = (now - last).total_seconds() / 3600
            decay = 0.95 ** (hours / 24)
        else:
            decay = 0.0

        p["score"] = win_rate * decay
    return sorted(posts, key=lambda p: p["score"], reverse=True)


def sort_controversial(posts: list[dict]) -> list[dict]:
    for p in posts:
        total = p["wins"] + p["losses"]
        if total == 0:
            p["score"] = 0.0
        else:
            balance = min(p["wins"], p["losses"]) / max(p["wins"], p["losses"], 1)
            p["score"] = balance * total
    return sorted(posts, key=lambda p: p["score"], reverse=True)
