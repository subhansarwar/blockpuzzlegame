# app/services/social/arena_service.py
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game.stats import UserGameStats
from app.models.social.leaderboard import WeeklyScore
from app.models.users.user import User
from app.schemas.social.arena import AllTimeLeaderboardResponse, LeaderboardEntry, WeeklyLeaderboardResponse

_TOP_N = 100
SortKey = Literal["points", "coins"]


def current_week_start(today: date | None = None) -> date:
    d = today or datetime.now(timezone.utc).date()
    return d - timedelta(days=d.weekday())  # Monday (UTC)


def _week_resets_at(week_start: date) -> datetime:
    return datetime.combine(week_start + timedelta(days=7), datetime.min.time(), tzinfo=timezone.utc)


async def add_weekly(db: AsyncSession, user_id: UUID, *, points: int = 0, coins: int = 0) -> None:
    week_start = current_week_start()
    result = await db.execute(
        select(WeeklyScore).where(WeeklyScore.user_id == user_id, WeeklyScore.week_start == week_start)
    )
    row = result.scalar_one_or_none()
    if not row:
        row = WeeklyScore(user_id=user_id, week_start=week_start)
        db.add(row)
        await db.flush()
    row.points_earned += points
    row.coins_earned += coins


async def get_weekly_leaderboard(db: AsyncSession, user: User, sort: SortKey = "points") -> WeeklyLeaderboardResponse:
    week_start = current_week_start()
    order_col = WeeklyScore.points_earned if sort == "points" else WeeklyScore.coins_earned

    result = await db.execute(
        select(WeeklyScore, User)
        .join(User, User.id == WeeklyScore.user_id)
        .where(WeeklyScore.week_start == week_start)
        .order_by(desc(order_col))
        .limit(_TOP_N)
    )
    rows = result.all()
    entries = [
        LeaderboardEntry(
            rank=i + 1, user_id=u.id, username=u.username, avatar_url=u.avatar_url,
            points=ws.points_earned, coins=ws.coins_earned,
        )
        for i, (ws, u) in enumerate(rows)
    ]

    my_rank = next((e.rank for e in entries if e.user_id == user.id), None)
    if my_rank is None:
        my_row = await db.execute(
            select(order_col).where(WeeklyScore.user_id == user.id, WeeklyScore.week_start == week_start)
        )
        my_value = my_row.scalar_one_or_none()
        if my_value is not None:
            count_result = await db.execute(
                select(func.count()).select_from(WeeklyScore)
                .where(WeeklyScore.week_start == week_start, order_col > my_value)
            )
            my_rank = count_result.scalar_one() + 1

    resets_at = _week_resets_at(week_start)
    remaining = int((resets_at - datetime.now(timezone.utc)).total_seconds())
    return WeeklyLeaderboardResponse(resets_at=resets_at, remaining_seconds=max(remaining, 0), my_rank=my_rank, entries=entries)


async def get_all_time_leaderboard(db: AsyncSession, user: User, sort: SortKey = "points") -> AllTimeLeaderboardResponse:
    order_col = UserGameStats.total_points if sort == "points" else UserGameStats.total_coins_earned

    result = await db.execute(
        select(UserGameStats, User)
        .join(User, User.id == UserGameStats.user_id)
        .order_by(desc(order_col))
        .limit(_TOP_N)
    )
    rows = result.all()
    entries = [
        LeaderboardEntry(
            rank=i + 1, user_id=u.id, username=u.username, avatar_url=u.avatar_url,
            points=s.total_points, coins=s.total_coins_earned,
        )
        for i, (s, u) in enumerate(rows)
    ]

    my_rank = next((e.rank for e in entries if e.user_id == user.id), None)
    if my_rank is None:
        my_row = await db.execute(select(order_col).where(UserGameStats.user_id == user.id))
        my_value = my_row.scalar_one_or_none()
        if my_value is not None:
            count_result = await db.execute(
                select(func.count()).select_from(UserGameStats).where(order_col > my_value)
            )
            my_rank = count_result.scalar_one() + 1

    return AllTimeLeaderboardResponse(my_rank=my_rank, entries=entries)
