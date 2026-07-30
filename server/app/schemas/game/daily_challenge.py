# app/schemas/game/daily_challenge.py
from datetime import date, datetime
from pydantic import BaseModel, Field


class DailyChallengeSubmitRequest(BaseModel):
    score: int = Field(ge=0, le=10_000_000)
    max_combo: int = Field(ge=0, le=1_000)
    lines_cleared: int = Field(ge=0, le=100_000)
    duration_seconds: int = Field(ge=0, le=86_400)


class DailyChallengeStateResponse(BaseModel):
    challenge_date: date
    day_number: int  # 1-7 within the weekly cycle
    coins_reward: int
    points_reward: int
    best_score_today: int
    is_claimed: bool
    resets_at: datetime  # next UTC midnight


class DailyChallengeSubmitResponse(BaseModel):
    best_score_today: int
    newly_claimed: bool
    coins_earned: int
    points_earned: int
    coins_balance: int
    total_points: int
