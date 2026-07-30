# app/schemas/game/time_attack.py
from pydantic import BaseModel, Field


class TimeAttackExtendRequest(BaseModel):
    ads_watched: int = Field(ge=0, le=5, description="Cumulative rewarded ads watched so far this session")


class TimeAttackExtendResponse(BaseModel):
    ads_watched: int
    time_limit_seconds: int


class TimeAttackSubmitRequest(BaseModel):
    score: int = Field(ge=0, le=10_000_000)
    max_combo: int = Field(ge=0, le=1_000)
    lines_cleared: int = Field(ge=0, le=100_000)
    duration_seconds: int = Field(ge=0, le=86_400)
    ads_watched: int = Field(default=0, ge=0, le=5)


class TimeAttackStateResponse(BaseModel):
    best_score: int
    last_score: int
    base_time_limit_seconds: int
    tier1_ads: int
    tier1_seconds: int
    tier2_ads: int
    tier2_seconds: int
