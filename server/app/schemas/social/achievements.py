# app/schemas/social/achievements.py
from datetime import datetime
from pydantic import BaseModel


class AchievementItem(BaseModel):
    code: str
    category: str
    tier: int
    title: str
    description: str | None
    icon_url: str | None
    points_threshold: int
    is_unlocked: bool
    is_claimed: bool
    claimed_at: datetime | None


class AchievementListResponse(BaseModel):
    completed_count: int
    total_count: int
    total_points: int
    achievements: list[AchievementItem]


class ClaimAchievementResponse(BaseModel):
    code: str
    claimed_at: datetime
