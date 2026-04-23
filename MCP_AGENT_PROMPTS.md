# MCP Agent Prompts for Hot Takes Tournament Assessment

This document contains specialized prompts for different MCP agents to assist with the Hot Takes Tournament assessment. Each agent has a focused responsibility and clear boundaries.

---

## Agent 1: Database Schema Agent

**Role:** Design and implement the matchups data layer

**Context:**
- Project: Hot Takes Tournament pairwise voting app
- Stack: Python 3.11, FastAPI, SQLite (stdlib sqlite3 only, no ORMs)
- Location: backend/app/database.py (DDL section), backend/app/routers/matchups.py
- Constraint: Must use raw SQL, no ORMs

**Current State:**
- Posts table exists: id, content, created_at
- Matchups table stub exists in DDL with: id, winner_id, loser_id, created_at
- Foreign keys enabled via PRAGMA on all connections
- Row factory set to sqlite3.Row

**Task:**
Review and validate the matchups table schema in backend/app/database.py. The current schema uses denormalized winner/loser columns. Ensure:
1. Foreign key constraints reference posts(id) with proper ON DELETE behavior
2. Check constraint prevents self-matchups (winner_id != loser_id)
3. Indexes support common query patterns (if needed)
4. Schema supports these queries efficiently:
   - Count wins per post
   - Count losses per post
   - Find last matchup timestamp per post
   - Insert new vote records

**Verification:**
- Run: pytest tests/test_schema.py::test_matchups_table_exists
- Check: Foreign key constraints are enforced
- Validate: No duplicate vote records possible

**Output:** Confirm schema correctness or suggest specific improvements with SQL DDL.

---

## Agent 2: Backend API Implementation Agent

**Role:** Implement FastAPI endpoint handlers

**Context:**
- Framework: FastAPI with Pydantic v2 validation
- Database: SQLite via context manager pattern (with connection() as conn:)
- Routers: backend/app/routers/posts.py and backend/app/routers/matchups.py
- Schemas: backend/app/schemas.py defines request/response models

**Current State:**
- GET /posts exists and works (returns all posts)
- POST /posts stub exists (needs validation and insert logic)
- GET /matchup stub exists (needs random pair selection)
- POST /matchup/vote stub exists (needs vote recording)
- GET /leaderboard stub exists (needs aggregation + ranking)

**Tasks:**

### 1. POST /posts endpoint
File: backend/app/routers/posts.py
- Validate: 5-200 character length (already in PostCreate schema)
- Insert: New post with content
- Return: Post object with id and created_at
- Error handling: Return 400 for validation failures

### 2. GET /matchup endpoint
File: backend/app/routers/matchups.py
- Query: Select two random posts
- Constraint: Never pair a post with itself
- Return: Matchup object with post_a and post_b
- Edge case: Handle when fewer than 2 posts exist

### 3. POST /matchup/vote endpoint
File: backend/app/routers/matchups.py
- Validate: winner_id and loser_id exist in posts table
- Validate: winner_id != loser_id (no self-votes)
- Insert: Record into matchups table
- Return: Success status
- Error handling: 404 for nonexistent posts, 400 for self-match

### 4. GET /leaderboard endpoint
File: backend/app/routers/matchups.py or posts.py
- Query parameter: ?sort= (recent|best|hot|controversial, default=best)
- Aggregate: wins, losses, last_matchup_at per post
- Call: Appropriate ranking.py function based on sort param
- Return: List of LeaderboardEntry objects with rank assigned
- Include: Posts with zero matchups (wins=0, losses=0)

**Code Pattern:**
```python
from app.database import connection
from app.schemas import PostCreate, Post

@router.post("/posts")
def create_post(post: PostCreate) -> Post:
    with connection() as conn:
        cursor = conn.execute(
            "INSERT INTO posts (content) VALUES (?)",
            (post.content,)
        )
        post_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM posts WHERE id = ?",
            (post_id,)
        ).fetchone()
        return Post.model_validate(row)
```

**Verification:**
- Run: pytest tests/test_api_and_ranking.py
- Check: All endpoint tests pass
- Validate: Error handling works for edge cases

---

## Agent 3: Ranking Algorithms Agent

**Role:** Implement four leaderboard sorting algorithms

**Context:**
- File: backend/app/ranking.py
- Input: List of dicts with keys: id, content, created_at, wins, losses, last_matchup_at
- Output: Same list sorted by computed score, with score field added to each dict
- Constraint: No external ranking libraries, no outbound HTTP

**Current Implementation:**
All four functions exist with basic implementations. Review and potentially enhance:

### 1. sort_recent(posts: list[dict]) -> list[dict]
- Current: Sorts by created_at descending
- Goal: Newest submissions first
- Consider: Already implemented correctly

### 2. sort_best(posts: list[dict]) -> list[dict]
- Current: Uses Laplace smoothing (wins+1)/(total+2)
- Goal: Highest win rate with confidence weighting
- Consider: Posts with more total votes should rank higher than same win rate with fewer votes
- Formula options: Wilson score, Bayesian average, confidence intervals

### 3. sort_hot(posts: list[dict]) -> list[dict]
- Current: win_rate × exponential_decay based on last_matchup_at
- Goal: Recent engagement × win rate (not post age, matchup recency)
- Consider: Posts with recent votes should rank higher even if old posts
- Handle: Posts with no matchups (last_matchup_at is None)

### 4. sort_controversial(posts: list[dict]) -> list[dict]
- Current: (min(wins,losses)/max(wins,losses)) × total_votes
- Goal: High volume + close win/loss split
- Consider: 50-50 split with 100 votes > 50-50 with 10 votes
- Consider: 100-0 split should rank LOW (not controversial)

**Test Requirements:**
- test_leaderboard_best_ranks_high_confidence_above_small_sample
- test_leaderboard_controversial_ranks_high_volume_balanced_above_low_volume_balanced
- test_leaderboard_hot_reflects_recent_matchups_not_post_age
- test_leaderboard_includes_zero_match_posts (all algorithms)

**Verification:**
Run: pytest tests/test_api_and_ranking.py -k leaderboard

---

## Agent 4: Frontend Implementation Agent

**Role:** Complete React component TODO markers

**Context:**
- Framework: React 18, Vite
- Constraints: useState, useEffect, fetch only (no Redux, Zustand, React Query, SWR)
- API proxy: /api → localhost:8000 (configured in vite.config.js)
- Files: frontend/src/views/Matchup.jsx, Submit.jsx, Leaderboard.jsx

**Current State:**
- App.jsx: Tab navigation shell exists
- views/Matchup.jsx: TODO markers for fetching and voting
- views/Submit.jsx: TODO markers for form submission
- views/Leaderboard.jsx: TODO markers for sort tabs and data display

### 1. Matchup.jsx
**Tasks:**
- Fetch: GET /api/matchup on mount and after each vote
- Display: Two posts side-by-side with vote buttons
- Vote: POST /api/matchup/vote with {winner_id, loser_id}
- UX: Disable buttons during vote submission, show loading state
- Flow: After vote succeeds, immediately fetch next matchup

**Snippet:**
```jsx
const [matchup, setMatchup] = useState(null)
const [loading, setLoading] = useState(false)

useEffect(() => {
  fetch('/api/matchup')
    .then(r => r.json())
    .then(setMatchup)
}, [])

const vote = (winnerId, loserId) => {
  setLoading(true)
  fetch('/api/matchup/vote', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({winner_id: winnerId, loser_id: loserId})
  })
  .then(() => fetch('/api/matchup'))
  .then(r => r.json())
  .then(m => { setMatchup(m); setLoading(false) })
}
```

### 2. Submit.jsx
**Tasks:**
- Form: Text input with 5-200 character validation
- Submit: POST /api/posts with {content}
- Success: Clear form, show success message
- Error: Display validation errors (too short, too long)
- UX: Disable submit during request

**Snippet:**
```jsx
const [content, setContent] = useState('')
const [message, setMessage] = useState('')

const submit = (e) => {
  e.preventDefault()
  fetch('/api/posts', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({content})
  })
  .then(r => r.json())
  .then(() => {
    setContent('')
    setMessage('Hot take submitted!')
  })
  .catch(err => setMessage(`Error: ${err.message}`))
}
```

### 3. Leaderboard.jsx
**Tasks:**
- Tabs: Four buttons - "New", "Top-rated", "Trending", "Divisive"
- Labels: Match exact names from requirements
- Subtitles: Display under each tab (see README table)
- Fetch: GET /api/leaderboard?sort={recent|best|hot|controversial}
- Display: Ranked list with rank, content, wins, losses, score
- State: Track current sort mode, refetch on tab switch

**Tab Mapping:**
| Button Label | Subtitle | API sort param |
|--------------|----------|----------------|
| New | Sorted by submission time | recent |
| Top-rated | Highest win rate with confidence | best |
| Trending | Recent engagement × win rate | hot |
| Divisive | Close win/loss splits with high vote volume | controversial |

**Snippet:**
```jsx
const [sort, setSort] = useState('best')
const [entries, setEntries] = useState([])

useEffect(() => {
  fetch(`/api/leaderboard?sort=${sort}`)
    .then(r => r.json())
    .then(setEntries)
}, [sort])

// Four buttons that call setSort('recent'), etc.
```

**Verification:**
- Run: pytest tests/test_frontend.py
- Manual: Start make dev, visit localhost:5173
- Check: All three views work, vote flow advances, leaderboard tabs switch

---

## Agent 5: Testing & Validation Agent

**Role:** Run tests, diagnose failures, suggest fixes

**Context:**
- Framework: pytest
- Command: make test or pytest tests/
- Progressive tests: Early tests (schema) unlock later tests (ranking, frontend)
- Fixtures: conftest.py provides client, db_conn, seeded_client, client_with_db

**Task Flow:**
1. Run: pytest --collect-only (see all test names)
2. Run: make test (see current pass/fail state)
3. For each failure:
   - Read test file to understand assertion
   - Check implementation against expected behavior
   - Suggest specific fix with file:line reference
4. Prioritize: Fix schema tests first, then API, then ranking, then frontend

**Common Failure Patterns:**
- Matchups table missing → Check database.py DDL
- Foreign key violation → Check PRAGMA foreign_keys = ON
- Validation error → Check Pydantic schema min_length/max_length
- Random pairing returns same post → Check matchup selection WHERE clause
- Ranking order wrong → Check ranking.py sort logic
- Frontend test timeout → Check if dev server is running

**Commands:**
```bash
pytest tests/test_schema.py -v                    # Schema tests only
pytest tests/test_api_and_ranking.py -v           # API + ranking tests
pytest tests/test_frontend.py -v                  # Frontend integration tests
pytest tests/ -k "leaderboard" -v                 # All leaderboard tests
pytest tests/ -x                                  # Stop on first failure
```

**Verification:**
All tests pass: pytest tests/ should show 100% pass rate

---

## Agent 6: End-to-End Integration Agent

**Role:** Verify full workflow and catch edge cases

**Context:**
- Stack: Backend (port 8000) + Frontend (port 5173)
- Command: make dev (starts both concurrently)
- Goal: Ensure all pieces work together

**Integration Checklist:**

### 1. Database Layer
- [ ] app.db created on startup
- [ ] 8 seed posts inserted
- [ ] Matchups table has foreign keys
- [ ] Foreign keys are enforced (test by trying to insert invalid winner_id)

### 2. Backend Endpoints
- [ ] GET /posts returns seeded data
- [ ] POST /posts accepts valid 5-200 char content
- [ ] POST /posts rejects <5 or >200 char content
- [ ] GET /matchup returns two different posts
- [ ] POST /matchup/vote records winner/loser
- [ ] POST /matchup/vote rejects nonexistent post IDs
- [ ] POST /matchup/vote rejects self-matches
- [ ] GET /leaderboard?sort=recent works
- [ ] GET /leaderboard?sort=best works
- [ ] GET /leaderboard?sort=hot works
- [ ] GET /leaderboard?sort=controversial works
- [ ] GET /leaderboard (no param) defaults to best

### 3. Frontend Views
- [ ] Matchup view loads two posts
- [ ] Voting advances to next matchup
- [ ] Submit view accepts text input
- [ ] Submit view shows success message
- [ ] Submit view validates length
- [ ] Leaderboard has four tab buttons
- [ ] Tab labels: "New", "Top-rated", "Trending", "Divisive"
- [ ] Tab switches update ranking
- [ ] New votes appear in leaderboard within 10s

### 4. Edge Cases
- [ ] Matchup when only 1 post exists (should error gracefully)
- [ ] Matchup when 0 posts exist (should error gracefully)
- [ ] Leaderboard includes posts with 0 votes
- [ ] Posts with same win rate are ranked by confidence/volume
- [ ] Hot ranking favors recent matchup activity, not post age
- [ ] Controversial ranking favors high volume + balanced splits

**Manual Test Flow:**
1. Start: make dev
2. Visit: http://localhost:5173
3. Submit: Create 2-3 new hot takes
4. Vote: Complete 10+ matchups
5. Leaderboard: Switch between all four tabs
6. Verify: Rankings change appropriately per tab
7. Submit: Try <5 char (should fail)
8. Submit: Try >200 char (should fail)

**Verification:**
End-to-end flow works without errors in console or terminal

---

## Agent 7: Performance & Code Quality Agent

**Role:** Review for efficiency and best practices

**Context:**
- Time pressure: 35 minutes coding time
- Assessment focus: Correctness > optimization
- Review after core functionality works

**Review Areas:**

### 1. Database Queries
- [ ] No N+1 queries in leaderboard aggregation
- [ ] Use single query with JOINs or subqueries for win/loss counts
- [ ] Index created_at if sorting by recent becomes slow (optional)
- [ ] Connection context manager used consistently

### 2. API Design
- [ ] Consistent error response format
- [ ] Proper HTTP status codes (200, 201, 400, 404)
- [ ] Pydantic validation catches bad input before DB query
- [ ] No SQL injection vulnerabilities (using parameterized queries)

### 3. Frontend
- [ ] No unnecessary re-renders
- [ ] Loading states prevent double-submission
- [ ] Fetch errors handled gracefully
- [ ] No hardcoded URLs (use /api prefix)

### 4. Code Organization
- [ ] Routers separated by resource (posts, matchups)
- [ ] Ranking logic isolated in ranking.py
- [ ] No business logic in main.py
- [ ] Tests don't depend on wall-clock timing

**Quick Wins:**
- Combine multiple queries into one for leaderboard aggregation
- Add error boundaries in frontend
- Use COALESCE for NULL handling in SQL
- Memoize expensive ranking calculations (if time permits)

**Skip (Not Worth Time):**
- Caching layer
- Database migrations
- User authentication
- Rate limiting
- Websockets for live updates

---

## Usage Notes for MCP Agents:

1. **Agent Activation**: Each agent should declare its role and boundaries
2. **Context Sharing**: Agents can reference other agents' output but should not duplicate work
3. **Progressive Work**: Start with Database → API → Ranking → Frontend → Testing
4. **Time Awareness**: 35 minutes total, prioritize working code over perfect code
5. **Test-Driven**: Run tests frequently to validate progress
6. **Communication**: Each agent should output file:line references for changes

**Coordination:**
- Database Agent completes schema before API Agent starts
- API Agent completes endpoints before Frontend Agent wires them
- Testing Agent validates after each major component
- Integration Agent runs final verification before submission
