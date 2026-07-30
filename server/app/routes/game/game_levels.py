# app/routes/game_levels.py
from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.schemas.game.levels import LevelCompleteResponse, LevelListResponse, LevelSubmitRequest
from app.services.game import levels_service

router = APIRouter(prefix="/game/levels", tags=["levels"])


@router.get("", response_model=LevelListResponse)
async def list_levels(db: SessionDep, user: CurrentUser):
    return await levels_service.list_levels(db, user)


@router.post("/{level_number}/submit", response_model=LevelCompleteResponse)
async def submit_level(level_number: int, req: LevelSubmitRequest, db: SessionDep, user: CurrentUser):
    return await levels_service.submit_level(db, user, level_number, req)
