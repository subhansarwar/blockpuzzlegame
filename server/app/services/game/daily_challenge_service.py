# app/services/game/daily_challenge_service.py
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game.daily_challenge import DailyChallengeClaim
from app.models.game.game_session import GameSession, GameMode
from app.models.users.user import User
from app.schemas.game.daily_challenge import (
    DailyChallengeStateResponse,
    DailyChallengeSubmitRequest,
    DailyChallengeSubmitResponse,
)
from app.services.game import stats_service
from app.services.social import arena_service

# day_number (ISO weekday, Mon=1..Sun=7) -> (coins_reward, points_reward)
_REWARDS = {
    1: (5000, 20),
    2: (5000, 20),
    3: (5000, 20),
    4: (5000, 20),
    5: (10000, 30),
    6: (15000, 30),
    7: (20000, 30),
}


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _day_number(d: date) -> int:
    return d.isoweekday()


def _resets_at(d: date) -> datetime:
    return datetime.combine(d + timedelta(days=1), time.min, tzinfo=timezone.utc)


async def _get_claim(db: AsyncSession, user_id, challenge_date: date) -> DailyChallengeClaim | None:
    result = await db.execute(
        select(DailyChallengeClaim).where(
            DailyChallengeClaim.user_id == user_id, DailyChallengeClaim.challenge_date == challenge_date
        )
    )
    return result.scalar_one_or_none()


async def get_state(db: AsyncSession, user: User) -> DailyChallengeStateResponse:
    today = _today()
    day_number = _day_number(today)
    coins_reward, points_reward = _REWARDS[day_number]
    claim = await _get_claim(db, user.id, today)
    return DailyChallengeStateResponse(
        challenge_date=today,
        day_number=day_number,
        coins_reward=coins_reward,
        points_reward=points_reward,
        best_score_today=claim.best_score if claim else 0,
        is_claimed=claim is not None,
        resets_at=_resets_at(today),
    )


async def submit_session(db: AsyncSession, user: User, req: DailyChallengeSubmitRequest) -> DailyChallengeSubmitResponse:
    today = _today()
    day_number = _day_number(today)
    coins_reward, points_reward = _REWARDS[day_number]

    claim = await _get_claim(db, user.id, today)
    newly_claimed = False
    coins_earned = 0
    points_earned = 0

    if not claim:
        claim = DailyChallengeClaim(
            user_id=user.id, challenge_date=today, day_number=day_number,
            best_score=req.score, coins_earned=coins_reward, points_earned=points_reward,
        )
        db.add(claim)
        newly_claimed = True
        coins_earned = coins_reward
        points_earned = points_reward
    elif req.score > claim.best_score:
        claim.best_score = req.score

    db.add(GameSession(
        user_id=user.id,
        mode=GameMode.daily_challenge,
        day_number=day_number,
        score=req.score,
        max_combo=req.max_combo,
        lines_cleared=req.lines_cleared,
        duration_seconds=req.duration_seconds,
        coins_earned=coins_earned,
        points_earned=points_earned,
    ))
    await stats_service.apply_session_result(db, user.id, score=req.score, max_combo=req.max_combo, lines_cleared=req.lines_cleared)

    if newly_claimed:
        stats = await stats_service.add_points(db, user.id, points_earned)
        stats = await stats_service.add_coins(db, user.id, coins_earned)
        await arena_service.add_weekly(db, user.id, points=points_earned, coins=coins_earned)
    else:
        stats = await stats_service.get_or_create_stats(db, user.id)

    await db.commit()

    return DailyChallengeSubmitResponse(
        best_score_today=claim.best_score,
        newly_claimed=newly_claimed,
        coins_earned=coins_earned,
        points_earned=points_earned,
        coins_balance=stats.coins_balance,
        total_points=stats.total_points,
    )
