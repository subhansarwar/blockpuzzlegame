# app/services/social/achievement_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.social.achievement import AchievementDefinition, UserAchievement
from app.models.game.stats import UserGameStats
from app.models.users.user import User
from app.schemas.social.achievements import AchievementItem, AchievementListResponse, ClaimAchievementResponse
from app.services.users import audit_service

COMBO_KINGS_TIERS = 20
COMBO_KINGS_STEP = 1000


def _seed_definitions() -> list[AchievementDefinition]:
    return [
        AchievementDefinition(
            code=f"combo_kings_{tier}",
            category="combo_kings",
            tier=tier,
            title=f"Combo King {tier}/{COMBO_KINGS_TIERS}",
            description=f"Earn {COMBO_KINGS_STEP * tier:,} lifetime points",
            points_threshold=COMBO_KINGS_STEP * tier,
        )
        for tier in range(1, COMBO_KINGS_TIERS + 1)
    ]


async def ensure_seeded(db: AsyncSession) -> None:
    result = await db.execute(select(AchievementDefinition.id).limit(1))
    if result.scalar_one_or_none():
        return
    for definition in _seed_definitions():
        db.add(definition)
    await db.commit()


async def list_achievements(db: AsyncSession, user: User) -> AchievementListResponse:
    result = await db.execute(select(UserGameStats.total_points).where(UserGameStats.user_id == user.id))
    total_points = result.scalar_one_or_none() or 0

    result = await db.execute(
        select(AchievementDefinition).order_by(AchievementDefinition.category, AchievementDefinition.tier)
    )
    definitions = result.scalars().all()

    result = await db.execute(select(UserAchievement).where(UserAchievement.user_id == user.id))
    claimed_by_id = {row.achievement_id: row for row in result.scalars().all()}

    items = [
        AchievementItem(
            code=d.code, category=d.category, tier=d.tier, title=d.title, description=d.description,
            icon_url=d.icon_url, points_threshold=d.points_threshold,
            is_unlocked=total_points >= d.points_threshold,
            is_claimed=d.id in claimed_by_id,
            claimed_at=claimed_by_id[d.id].claimed_at if d.id in claimed_by_id else None,
        )
        for d in definitions
    ]

    return AchievementListResponse(
        completed_count=len(claimed_by_id), total_count=len(definitions), total_points=total_points, achievements=items,
    )


async def claim_achievement(db: AsyncSession, user: User, code: str) -> ClaimAchievementResponse:
    result = await db.execute(select(AchievementDefinition).where(AchievementDefinition.code == code))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Achievement not found")

    result = await db.execute(select(UserGameStats.total_points).where(UserGameStats.user_id == user.id))
    total_points = result.scalar_one_or_none() or 0
    if total_points < definition.points_threshold:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Achievement not yet unlocked")

    result = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == user.id, UserAchievement.achievement_id == definition.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Achievement already claimed")

    claim = UserAchievement(user_id=user.id, achievement_id=definition.id)
    db.add(claim)
    await audit_service.log_event(db, user_id=user.id, event="achievement_claim", status="success", detail=code)
    await db.commit()
    await db.refresh(claim)
    return ClaimAchievementResponse(code=code, claimed_at=claim.claimed_at)
