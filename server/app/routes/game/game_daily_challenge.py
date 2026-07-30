# app/routes/game_daily_challenge.py
from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.schemas.game.daily_challenge import (
    DailyChallengeStateResponse,
    DailyChallengeSubmitRequest,
    DailyChallengeSubmitResponse,
)
from app.services.game import daily_challenge_service

router = APIRouter(prefix="/game/daily-challenge", tags=["daily-challenge"])


@router.get("", response_model=DailyChallengeStateResponse)
async def get_state(db: SessionDep, user: CurrentUser):
    return await daily_challenge_service.get_state(db, user)


@router.post("/submit", response_model=DailyChallengeSubmitResponse)
async def submit(req: DailyChallengeSubmitRequest, db: SessionDep, user: CurrentUser):
    return await daily_challenge_service.submit_session(db, user, req)
