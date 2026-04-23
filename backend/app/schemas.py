# TenX Assessment — do not modify this header
"""Pydantic request/response models — the HTTP contract."""
from pydantic import BaseModel, ConfigDict, Field


class Post(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_at: str


class PostCreate(BaseModel):
    content: str = Field(min_length=5, max_length=200)


class Matchup(BaseModel):
    post_a: Post
    post_b: Post


class VoteRequest(BaseModel):
    winner_id: int
    loser_id: int


class LeaderboardEntry(BaseModel):
    id: int
    content: str
    wins: int
    losses: int
    score: float
    rank: int
