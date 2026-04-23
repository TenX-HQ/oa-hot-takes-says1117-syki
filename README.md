## TenX AI Assistant (Required)

**You must use the TenX AI assistant for this assessment.** It is pre-configured for
this environment and required for evaluation.

**Launch it** (new terminal tab):

```bash
tenx-ai
```

**Rules**
- The assistant is your primary tool. Use it freely — that is the point.
- Do not use ChatGPT, Claude.ai, Gemini, Copilot Chat, or any other external AI.
- Browser searches and documentation are allowed.

**What is evaluated**
- Solution quality (correctness, robustness, code health)
- Your understanding of what you built (free-response questions at submission)
- How you worked with AI (the assistant logs the session automatically)

**Submission** — when your time is up or you are done:

```bash
tenx-submit
```

---

# Hot Takes Tournament

A pairwise-voting web app where users submit short opinions ("hot takes"), vote on head-to-head matchups between two takes, and a leaderboard ranks every take by its matchup history.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLite (stdlib `sqlite3`) |
| Frontend | React 18, Vite |
| Validation | Pydantic v2 |

## Make Commands

`make dev` starts backend (8000) and frontend (5173) together. Other targets: `make backend`, `make frontend`, `make seed`, `make reset-db`, `make test`, `make verify`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/posts` | List all posts |
| `POST` | `/posts` | Submit a new hot take (5–200 characters) |
| `GET` | `/matchup` | Get two random posts for a head-to-head vote |
| `POST` | `/matchup/vote` | Record a vote with a winner and loser |
| `GET` | `/leaderboard?sort=...` | Ranked leaderboard; accepts `recent`, `best`, `hot`, `controversial`; default `best` |
| `GET` | `/health` | Health check |

## Assessment Task

Build the app end-to-end: the matchups data layer, all backend endpoints, four ranking algorithms, and the frontend views that tie them together.

The backend has a working `GET /posts` anchor and stub handlers for everything else. The frontend has scaffolded views with `TODO` markers. Your job is to complete both sides.

The leaderboard supports four sort modes. The frontend tabs use these exact labels:

| Tab label | Subtitle | Sort param |
|-----------|----------|------------|
| **New** | Sorted by submission time | `recent` |
| **Top-rated** | Highest win rate with confidence | `best` |
| **Trending** | Recent engagement × win rate | `hot` |
| **Divisive** | Close win/loss splits with high vote volume | `controversial` |

Each sort mode requires its own ranking formula in `ranking.py`. How you implement them — what signals you weight, how you define recency, how you handle posts with no votes yet — is your decision.

**Hard constraints:**
- Backend: FastAPI, stdlib `sqlite3` only — no ORMs
- Ranking: all logic in `ranking.py`, no outbound HTTP from that module, no external ranking libraries
- Frontend: `useState`, `useEffect`, and `fetch` only — no state-management libraries (Redux, Zustand), no data-fetching libraries (React Query, SWR)

**Time limit: 35 minutes coding / 10 minutes free-response.**

This problem is structured progressively — running `pytest --collect-only` and `make test` will show you the areas of work.

## Before coding

1. Read every file under `backend/app/` — understand what is given, what is stubbed, and what is missing.
2. Read every file under `frontend/src/` — the views have scaffolded shells with `TODO` markers.
3. Read all files in `tests/`.
4. Run `pytest --collect-only` to see the full test map.
5. Run `make test` to see the baseline pass/fail state.

## Project Structure

`backend/app/` holds `main.py`, `config.py`, `database.py`, `schemas.py`, `ranking.py`, and `routers/`. `frontend/src/` holds `App.jsx`, `api.js`, and `views/`. `tests/` is at the repo root.

Think carefully about what happens at the boundaries — these decisions are yours to make.
