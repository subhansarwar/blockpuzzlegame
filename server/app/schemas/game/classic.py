# app/schemas/game/classic.py
from pydantic import BaseModel, Field
from app.models.game.game_session import Difficulty


class ClassicSubmitRequest(BaseModel):
    difficulty: Difficulty
    score: int = Field(ge=0, le=10_000_000)
    max_combo: int = Field(ge=0, le=1_000)
    lines_cleared: int = Field(ge=0, le=100_000)
    duration_seconds: int = Field(ge=0, le=86_400)


class ClassicDifficultyBest(BaseModel):
    difficulty: Difficulty
    best_score: int
    last_score: int


class ClassicStateResponse(BaseModel):
    difficulties: list[ClassicDifficultyBest]
