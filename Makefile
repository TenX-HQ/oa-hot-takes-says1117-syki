.PHONY: dev backend frontend test verify seed reset-db

dev:  ## Start backend (port 8000) and frontend (port 5173)
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev

backend:  ## Start backend on port 8000
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:  ## Start frontend on port 5173 (proxies /api to :8000)
	cd frontend && npm run dev

seed:  ## Populate SQLite DB with sample posts and matchups
	python -m seed.seed

reset-db:  ## Delete the local SQLite database file
	rm -f app.db

test:  ## Run pytest suite
	pytest

verify: test  ## Run tests (CI alias)
	@echo "All checks passed"
