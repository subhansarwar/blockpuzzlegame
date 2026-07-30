# app/routes/profile.py
from fastapi import APIRouter, File, UploadFile

from app.core.deps import CurrentUser, SessionDep
from app.schemas.game.stats import StatsResponse
from app.schemas.users.auth import MessageResponse
from app.schemas.users.preferences import PreferenceResponse, PreferenceUpdate
from app.schemas.users.profile import (AvatarResponse, DeleteAccountRequest, ProfileResponse, ResetProgressResponse, nameUpdateRequest,)
from app.services.game.stats_service import get_stats_response
from app.services.users.profile_service_api import get_profile, get_preferences, update_name, update_avatar, delete_account, delete_avatar, update_preferences, reset_progress

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.get("/read", response_model=ProfileResponse)
async def api_get_profile(db: SessionDep, user: CurrentUser):
    return await get_profile(db, user)

@router.patch("/update/name", response_model=ProfileResponse)
async def api_update_names(req: nameUpdateRequest, db: SessionDep, user: CurrentUser):
    return await update_name(db, user, req.name)

@router.put("/update/avatar", response_model=AvatarResponse)
async def api_update_avatar(db: SessionDep, user: CurrentUser, file: UploadFile = File(...)):
    content = await file.read()
    return await update_avatar(db, user, content, file.content_type)

@router.delete("/delete/avatar", response_model=AvatarResponse)
async def api_delete_avatar(db: SessionDep, user: CurrentUser):
    return await delete_avatar(db, user)

@router.get("/read/preferences", response_model=PreferenceResponse)
async def api_get_preferences(db: SessionDep, user: CurrentUser):
    return await get_preferences(db, user)

@router.patch("/update/preferences", response_model=PreferenceResponse)
async def api_update_preferences(update: PreferenceUpdate, db: SessionDep, user: CurrentUser):
    return await update_preferences(db, user, update)

@router.get("/read/stats", response_model=StatsResponse)
async def api_get_stats(db: SessionDep, user: CurrentUser):
    return await get_stats_response(db, user.id)

@router.post("/reset-progress", response_model=ResetProgressResponse)
async def api_reset_progress(db: SessionDep, user: CurrentUser):
    await reset_progress(db, user)
    return ResetProgressResponse(message="All progress has been reset")

@router.delete("/delete/account", response_model=MessageResponse)
async def api_delete_accounts(req: DeleteAccountRequest, db: SessionDep, user: CurrentUser):
    await delete_account(db, user, req.password)
    return MessageResponse(message="Account deleted")
