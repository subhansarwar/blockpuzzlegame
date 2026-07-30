# app/schemas/game/levels.py
from pydantic import BaseModel, Field


class LevelSubmitRequest(BaseModel):
    score: int = Field(ge=0, le=10_000_000)
    max_combo: int = Field(ge=0, le=1_000)
    lines_cleared: int = Field(ge=0, le=100_000)
    duration_seconds: int = Field(ge=0, le=86_400)


class LevelCompleteResponse(BaseModel):
    level_number: int
    points_earned: int
    milestone_coins: str  # arbitrary-precision "treasure" display value for the level-up popup — not a wallet credit
    popup_message: str
    next_level: int | None  # null once level 100 is complete
    level_mode_total_points: int
    total_points: int  # updated global lifetime points balance


class LevelInfo(BaseModel):
    level_number: int
    points_reward: int
    milestone_coins: str
    is_completed: bool
    is_unlocked: bool


class LevelListResponse(BaseModel):
    current_level: int
    best_score: int
    last_score: int
    levels: list[LevelInfo]
