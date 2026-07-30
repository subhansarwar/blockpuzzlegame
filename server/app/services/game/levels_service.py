# app/services/game/levels_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.game.levels import UserLevelState, LevelProgress
from app.models.game.game_session import GameSession, GameMode
from app.models.users.user import User
from app.schemas.game.levels import LevelCompleteResponse, LevelInfo, LevelListResponse, LevelSubmitRequest
from app.services.game import stats_service

MAX_LEVEL = 100
COINS_PER_LEVEL = 500
POINTS_PER_LEVEL = 10

# Cycled by level number so consecutive levels don't repeat the same line.
_POPUP_MESSAGES = [
    "Block Master! Level {n} crushed!",
    "On fire! Level {n} complete!",
    "Smooth clear! Level {n} done!",
    "Level {n} conquered like a pro!",
    "Unstoppable! Level {n} cleared!",
    "Boom! Level {n} in the bag!",
    "Nice combo run! Level {n} finished!",
    "Legendary! Level {n} beaten!",
    "Flawless! Level {n} complete!",
    "You're on a roll! Level {n} down!",
    "Puzzle master strikes again! Level {n}!",
    "Incredible! Level {n} cleared with style!",
    "Champion moves! Level {n} complete!",
    "Sharp thinking! Level {n} solved!",
    "Victory! Level {n} is history!",
    "Brilliant! Level {n} wrapped up!",
    "Crushing it! Level {n} done!",
    "Next-level skills! Level {n} cleared!",
    "Sensational! Level {n} complete!",
    "Grandmaster clear! Level {n} finished!",
]


def milestone_coins(level_number: int) -> int:
    """
    Display-only 'treasure milestone' number for the level-up popup.
    cumulative(n) = (cumulative(n-1) + 500) * n — matches the spec's worked examples for
    levels 1-3 exactly, but grows combinatorially (~500*e*n!) so it is NEVER credited to a
    real wallet. Points (10 * level, linear) are the only reward that hits the user's balance.
    """
    total = 0
    for n in range(1, level_number + 1):
        total = (total + COINS_PER_LEVEL) * n
    return total


def popup_message(level_number: int) -> str:
    template = _POPUP_MESSAGES[(level_number - 1) % len(_POPUP_MESSAGES)]
    return template.format(n=level_number)


async def get_or_create_state(db: AsyncSession, user_id) -> UserLevelState:
    result = await db.execute(select(UserLevelState).where(UserLevelState.user_id == user_id))
    row = result.scalar_one_or_none()
    if not row:
        row = UserLevelState(user_id=user_id)
        db.add(row)
        await db.flush()
    return row


async def list_levels(db: AsyncSession, user: User) -> LevelListResponse:
    state = await get_or_create_state(db, user.id)
    result = await db.execute(select(LevelProgress.level_number).where(LevelProgress.user_id == user.id))
    completed = {row[0] for row in result.all()}

    levels = [
        LevelInfo(
            level_number=n,
            points_reward=POINTS_PER_LEVEL * n,
            milestone_coins=str(milestone_coins(n)),
            is_completed=n in completed,
            is_unlocked=n <= state.current_level,
        )
        for n in range(1, MAX_LEVEL + 1)
    ]
    return LevelListResponse(
        current_level=state.current_level, best_score=state.best_score, last_score=state.last_score, levels=levels
    )


async def submit_level(db: AsyncSession, user: User, level_number: int, req: LevelSubmitRequest) -> LevelCompleteResponse:
    state = await get_or_create_state(db, user.id)

    if level_number > MAX_LEVEL:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="All 100 levels are already complete")
    if level_number != state.current_level:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"You must play level {state.current_level} next")

    already = await db.execute(
        select(LevelProgress.id).where(LevelProgress.user_id == user.id, LevelProgress.level_number == level_number)
    )
    if already.scalar_one_or_none():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Level already completed")

    points_earned = POINTS_PER_LEVEL * level_number
    coins_display = milestone_coins(level_number)

    state.last_score = req.score
    if req.score > state.best_score:
        state.best_score = req.score
    state.total_points_earned += points_earned
    if level_number < MAX_LEVEL:
        state.current_level = level_number + 1

    db.add(LevelProgress(user_id=user.id, level_number=level_number, score=req.score, points_earned=points_earned))
    db.add(GameSession(
        user_id=user.id,
        mode=GameMode.levels,
        level_number=level_number,
        score=req.score,
        max_combo=req.max_combo,
        lines_cleared=req.lines_cleared,
        duration_seconds=req.duration_seconds,
        points_earned=points_earned,
    ))
    await stats_service.apply_session_result(db, user.id, score=req.score, max_combo=req.max_combo, lines_cleared=req.lines_cleared)
    stats = await stats_service.add_points(db, user.id, points_earned)

    await db.commit()

    return LevelCompleteResponse(
        level_number=level_number,
        points_earned=points_earned,
        milestone_coins=str(coins_display),
        popup_message=popup_message(level_number),
        next_level=level_number + 1 if level_number < MAX_LEVEL else None,
        level_mode_total_points=state.total_points_earned,
        total_points=stats.total_points,
    )
