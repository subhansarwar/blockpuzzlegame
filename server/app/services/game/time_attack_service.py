# app/services/game/time_attack_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.game.time_attack import TimeAttackBest
from app.models.game.game_session import GameSession, GameMode
from app.models.users.user import User
from app.schemas.game.time_attack import (
    TimeAttackExtendResponse,
    TimeAttackStateResponse,
    TimeAttackSubmitRequest,
)
from app.services.game import stats_service


def compute_time_limit(ads_watched: int) -> int:
    if ads_watched >= settings.TIME_ATTACK_TIER2_ADS:
        return settings.TIME_ATTACK_TIER2_SECONDS
    if ads_watched >= settings.TIME_ATTACK_TIER1_ADS:
        return settings.TIME_ATTACK_TIER1_SECONDS
    return settings.TIME_ATTACK_BASE_SECONDS


def extend_session(ads_watched: int) -> TimeAttackExtendResponse:
    return TimeAttackExtendResponse(ads_watched=ads_watched, time_limit_seconds=compute_time_limit(ads_watched))


async def get_or_create_best(db: AsyncSession, user_id) -> TimeAttackBest:
    result = await db.execute(select(TimeAttackBest).where(TimeAttackBest.user_id == user_id))
    row = result.scalar_one_or_none()
    if not row:
        row = TimeAttackBest(user_id=user_id)
        db.add(row)
        await db.flush()
    return row


async def get_state(db: AsyncSession, user: User) -> TimeAttackStateResponse:
    best = await get_or_create_best(db, user.id)
    return TimeAttackStateResponse(
        best_score=best.best_score,
        last_score=best.last_score,
        base_time_limit_seconds=settings.TIME_ATTACK_BASE_SECONDS,
        tier1_ads=settings.TIME_ATTACK_TIER1_ADS,
        tier1_seconds=settings.TIME_ATTACK_TIER1_SECONDS,
        tier2_ads=settings.TIME_ATTACK_TIER2_ADS,
        tier2_seconds=settings.TIME_ATTACK_TIER2_SECONDS,
    )


async def submit_session(db: AsyncSession, user: User, req: TimeAttackSubmitRequest) -> TimeAttackStateResponse:
    best = await get_or_create_best(db, user.id)
    best.last_score = req.score
    if req.score > best.best_score:
        best.best_score = req.score

    db.add(GameSession(
        user_id=user.id,
        mode=GameMode.time_attack,
        score=req.score,
        max_combo=req.max_combo,
        lines_cleared=req.lines_cleared,
        duration_seconds=req.duration_seconds,
        ads_watched=req.ads_watched,
    ))
    await stats_service.apply_session_result(db, user.id, score=req.score, max_combo=req.max_combo, lines_cleared=req.lines_cleared)
    await db.commit()
    return await get_state(db, user)
