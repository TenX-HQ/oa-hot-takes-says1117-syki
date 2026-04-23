# TenX Assessment — do not modify this header
"""FastAPI application factory.

Wires routers, CORS, and DB initialization on startup. No route handlers
live here — they belong in app.routers.*.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import matchups, posts


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Hot Takes Tournament", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts.router)
app.include_router(matchups.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
