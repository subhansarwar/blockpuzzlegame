# app/services/users/notification_service.py
import asyncio

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.fcm import send_multicast
from app.models.users.device_token import DeviceToken
from app.models.users.preferences import UserPreference


async def _get_tokens_for_user(user_id: str) -> list[str]:
    async with SessionLocal() as db:
        result = await db.execute(select(UserPreference.notifications_enabled).where(UserPreference.user_id == user_id))
        enabled = result.scalar_one_or_none()
        if enabled is False:
            return []
        result = await db.execute(select(DeviceToken.token).where(DeviceToken.user_id == user_id))
        return [row[0] for row in result.all()]


@celery_app.task(name="app.services.users.notification_service.send_push_to_user")
def send_push_to_user(user_id: str, title: str, body: str) -> None:
    tokens = asyncio.run(_get_tokens_for_user(user_id))
    if tokens:
        send_multicast(tokens, title=title, body=body)
