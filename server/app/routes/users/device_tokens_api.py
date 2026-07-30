# app/routes/device_tokens.py
from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.schemas.users.auth import MessageResponse
from app.schemas.users.device_token import DeviceTokenCreate, DeviceTokenDelete
from app.services.users import device_token_service

router = APIRouter(prefix="/device-tokens", tags=["device-tokens"])


@router.post("", response_model=MessageResponse)
async def register(req: DeviceTokenCreate, db: SessionDep, user: CurrentUser):
    await device_token_service.register(db, user, req)
    return MessageResponse(message="Device token registered")


@router.delete("", response_model=MessageResponse)
async def unregister(req: DeviceTokenDelete, db: SessionDep, user: CurrentUser):
    await device_token_service.unregister(db, user, req)
    return MessageResponse(message="Device token removed")
