# app/routes/game_time_attack.py
from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.schemas.game.time_attack import (
    TimeAttackExtendRequest,
    TimeAttackExtendResponse,
    TimeAttackStateResponse,
    TimeAttackSubmitRequest,
)
from app.services.game import time_attack_service

router = APIRouter(prefix="/game/time-attack", tags=["time-attack"])


@router.get("", response_model=TimeAttackStateResponse)
async def get_state(db: SessionDep, user: CurrentUser):
    return await time_attack_service.get_state(db, user)


@router.post("/extend", response_model=TimeAttackExtendResponse)
async def extend(req: TimeAttackExtendRequest, user: CurrentUser):
    return time_attack_service.extend_session(req.ads_watched)


@router.post("/submit", response_model=TimeAttackStateResponse)
async def submit(req: TimeAttackSubmitRequest, db: SessionDep, user: CurrentUser):
    return await time_attack_service.submit_session(db, user, req)
