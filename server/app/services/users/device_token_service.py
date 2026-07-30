# app/services/users/device_token_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.device_token import DeviceToken
from app.models.users.user import User
from app.schemas.users.device_token import DeviceTokenCreate, DeviceTokenDelete


async def register(db: AsyncSession, user: User, req: DeviceTokenCreate) -> None:
    result = await db.execute(select(DeviceToken).where(DeviceToken.token == req.token))
    row = result.scalar_one_or_none()
    if row:
        row.user_id = user.id
        row.platform = req.platform
    else:
        db.add(DeviceToken(user_id=user.id, token=req.token, platform=req.platform))
    await db.commit()


async def unregister(db: AsyncSession, user: User, req: DeviceTokenDelete) -> None:
    result = await db.execute(select(DeviceToken).where(DeviceToken.token == req.token, DeviceToken.user_id == user.id))
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
