# Hot Takes Tournament

## Purpose
A pairwise-voting web app where users submit short opinions, vote on head-to-head matchups, and a leaderboard ranks every take by its matchup history. Built as a TenX timed assessment: 35 minutes coding + 10 minutes free-response.

## Stack
- Backend: Python 3.11, FastAPI, SQLite (stdlib `sqlite3` only, no ORMs)
- Frontend: React 18, Vite
- Validation: Pydantic v2

## Structure
- `backend/app/` — FastAPI application
  - `main.py` — app factory, CORS, router wiring
  - `database.py` — SQLite connection factory, DDL, seed data
  - `schemas.py` — Pydantic request/response models
  - `ranking.py` — four ranking algorithms (recent, best, hot, controversial)
  - `routers/` — endpoint handlers (posts, matchups)
- `frontend/src/` — React views
  - `App.jsx` — tab navigation shell
  - `views/` — Matchup, Submit, Leaderboard components
  - `api.js` — fetch wrappers (proxies /api → :8000)
- `tests/` — pytest suite at repo root (uses `backend` as pythonpath)
- `seed/` — optional data population script

## Commands
```bash
make dev        # Start backend (8000) + frontend (5173) together
make backend    # Backend only
make frontend   # Frontend only (proxies /api to :8000)
make test       # Run pytest suite
make seed       # Populate sample data
make reset-db   # Delete app.db
```

## Conventions
- Every file starts with `# TenX Assessment — do not modify this header`
- Backend uses context manager pattern: `with connection() as conn:`
- SQLite connections require `PRAGMA foreign_keys = ON` (set in `get_connection`)
- Row factory is `sqlite3.Row` for dict-like access (`row["column"]`)
- Routers live in `app.routers.*`, not in `main.py`
- Pydantic models use `ConfigDict(from_attributes=True)` for ORM-like construction
- Frontend: `useState` / `useEffect` / `fetch` only — no Redux, Zustand, React Query, SWR
- Ranking: all logic in `ranking.py`, no outbound HTTP, no external ranking libraries

## Gotchas
- **Matchups table schema is candidate's choice**: denormalized `(winner_id, loser_id)` or normalized `(post_a_id, post_b_id, winner_id)`. Tests are shape-agnostic — any schema with at least one FK to `posts(id)` passes.
- **Ranking algorithms are open-ended**: what signals to weight, how to define recency, how to handle zero-vote posts — all your call. The only constraint: no external ranking libraries.
- **Four leaderboard sort modes**: `recent` (submission time), `best` (win rate + confidence), `hot` (recent engagement × win rate), `controversial` (close splits + high vote volume). How you implement each is unspecified.
- **Frontend tabs use exact labels**: "New", "Top-rated", "Trending", "Divisive" (map to sort params `recent`, `best`, `hot`, `controversial`).
- **Tests are progressive**: run `pytest --collect-only` to see the full map. Early tests (schema, basic endpoints) unlock later tests (ranking, frontend integration).
- **`init_db()` is idempotent**: seeds 8 starter posts only if the posts table is empty. Safe to call on every startup.
- **Database path**: defaults to `app.db` at repo root, overridable via `DATABASE_URL` env var.

## API Endpoints (from README)
```
GET  /posts              List all posts
POST /posts              Submit a new hot take (5–200 characters)
GET  /matchup            Get two random posts for voting
POST /matchup/vote       Record a vote (winner + loser)
GET  /leaderboard?sort=  Ranked leaderboard (recent|best|hot|controversial; default=best)
GET  /health             Health check
```

## Testing Notes
- Pytest uses `backend` as pythonpath (see `pyproject.toml`)
- Fixtures in `tests/conftest.py` provide `db_conn`, `seeded_client`, etc.
- Tests allow flexible schemas but expect foreign keys and certain endpoint contracts
- Run `make test` to see baseline pass/fail state before coding
