# app/routes/game_classic.py
from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.schemas.game.classic import ClassicStateResponse, ClassicSubmitRequest
from app.services.game import classic_service

router = APIRouter(prefix="/game/classic", tags=["classic"])


@router.get("", response_model=ClassicStateResponse)
async def get_state(db: SessionDep, user: CurrentUser):
    return await classic_service.get_state(db, user)


@router.post("/submit", response_model=ClassicStateResponse)
async def submit(req: ClassicSubmitRequest, db: SessionDep, user: CurrentUser):
    return await classic_service.submit_session(db, user, req)
