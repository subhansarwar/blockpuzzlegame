# app/routes/arena.py
from typing import Literal

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, SessionDep
from app.schemas.social.arena import AllTimeLeaderboardResponse, WeeklyLeaderboardResponse
from app.services.social import arena_service

router = APIRouter(prefix="/arena", tags=["arena"])


@router.get("/weekly", response_model=WeeklyLeaderboardResponse)
async def weekly(
    db: SessionDep,
    user: CurrentUser,
    sort: Literal["points", "coins"] = Query(default="points"),
):
    return await arena_service.get_weekly_leaderboard(db, user, sort=sort)


@router.get("/all-time", response_model=AllTimeLeaderboardResponse)
async def all_time(
    db: SessionDep,
    user: CurrentUser,
    sort: Literal["points", "coins"] = Query(default="points"),
):
    return await arena_service.get_all_time_leaderboard(db, user, sort=sort)
