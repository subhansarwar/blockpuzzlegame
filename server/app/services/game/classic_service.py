# app/services/game/classic_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game.classic import ClassicBest
from app.models.game.game_session import GameSession, GameMode, Difficulty
from app.models.users.user import User
from app.schemas.game.classic import ClassicDifficultyBest, ClassicStateResponse, ClassicSubmitRequest
from app.services.game import stats_service


async def _get_or_create(db: AsyncSession, user_id, difficulty: Difficulty) -> ClassicBest:
    result = await db.execute(
        select(ClassicBest).where(ClassicBest.user_id == user_id, ClassicBest.difficulty == difficulty)
    )
    row = result.scalar_one_or_none()
    if not row:
        row = ClassicBest(user_id=user_id, difficulty=difficulty)
        db.add(row)
        await db.flush()
    return row


async def get_state(db: AsyncSession, user: User) -> ClassicStateResponse:
    entries = []
    for difficulty in Difficulty:
        row = await _get_or_create(db, user.id, difficulty)
        entries.append(ClassicDifficultyBest(difficulty=difficulty, best_score=row.best_score, last_score=row.last_score))
    await db.commit()
    return ClassicStateResponse(difficulties=entries)


async def submit_session(db: AsyncSession, user: User, req: ClassicSubmitRequest) -> ClassicStateResponse:
    row = await _get_or_create(db, user.id, req.difficulty)
    row.last_score = req.score
    if req.score > row.best_score:
        row.best_score = req.score

    db.add(GameSession(
        user_id=user.id,
        mode=GameMode.classic,
        difficulty=req.difficulty,
        score=req.score,
        max_combo=req.max_combo,
        lines_cleared=req.lines_cleared,
        duration_seconds=req.duration_seconds,
    ))
    await stats_service.apply_session_result(db, user.id, score=req.score, max_combo=req.max_combo, lines_cleared=req.lines_cleared)
    await db.commit()
    return await get_state(db, user)
