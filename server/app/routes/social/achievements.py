# app/routes/achievements.py
from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.schemas.social.achievements import AchievementListResponse, ClaimAchievementResponse
from app.services.social import achievement_service

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("", response_model=AchievementListResponse)
async def list_achievements(db: SessionDep, user: CurrentUser):
    return await achievement_service.list_achievements(db, user)


@router.post("/{code}/claim", response_model=ClaimAchievementResponse)
async def claim(code: str, db: SessionDep, user: CurrentUser):
    return await achievement_service.claim_achievement(db, user, code)
