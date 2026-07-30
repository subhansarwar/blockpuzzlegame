# app/schemas/social/arena.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    avatar_url: str | None
    points: int
    coins: int


class WeeklyLeaderboardResponse(BaseModel):
    resets_at: datetime
    remaining_seconds: int
    my_rank: int | None
    entries: list[LeaderboardEntry]


class AllTimeLeaderboardResponse(BaseModel):
    my_rank: int | None
    entries: list[LeaderboardEntry]
