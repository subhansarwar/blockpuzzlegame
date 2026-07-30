# app/services/game/stats_service.py
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game.stats import UserGameStats
from app.schemas.game.stats import StatsResponse


async def get_or_create_stats(db: AsyncSession, user_id: UUID) -> UserGameStats:
    result = await db.execute(select(UserGameStats).where(UserGameStats.user_id == user_id))
    stats = result.scalar_one_or_none()
    if not stats:
        stats = UserGameStats(user_id=user_id)
        db.add(stats)
        await db.flush()
    return stats


async def apply_session_result(db: AsyncSession, user_id: UUID, *, score: int, max_combo: int, lines_cleared: int) -> UserGameStats:
    stats = await get_or_create_stats(db, user_id)
    if score > stats.all_time_high_score:
        stats.all_time_high_score = score
    if max_combo > stats.max_combo:
        stats.max_combo = max_combo
    stats.total_lines_cleared += lines_cleared
    return stats


async def add_points(db: AsyncSession, user_id: UUID, amount: int) -> UserGameStats:
    stats = await get_or_create_stats(db, user_id)
    stats.points_balance += amount
    stats.total_points += amount
    return stats


async def spend_points(db: AsyncSession, user_id: UUID, amount: int) -> UserGameStats:
    await get_or_create_stats(db, user_id)
    # Row lock held until the caller commits, so two concurrent spends can't both
    # read the same balance and overdraw it.
    result = await db.execute(select(UserGameStats).where(UserGameStats.user_id == user_id).with_for_update())
    stats = result.scalar_one()
    if stats.points_balance < amount:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Not enough points")
    stats.points_balance -= amount
    return stats


async def add_coins(db: AsyncSession, user_id: UUID, amount: int) -> UserGameStats:
    stats = await get_or_create_stats(db, user_id)
    stats.coins_balance += amount
    stats.total_coins_earned += amount
    return stats


async def get_stats_response(db: AsyncSession, user_id: UUID) -> StatsResponse:
    stats = await get_or_create_stats(db, user_id)
    return StatsResponse(
        all_time_high_score=stats.all_time_high_score,
        max_combo=stats.max_combo,
        total_lines_cleared=stats.total_lines_cleared,
        total_points=stats.total_points,
    )
