# app/services/users/maintenance_service.py
import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.users.otp import EmailOTP
from app.models.users.refresh_tokens import RefreshToken


async def _cleanup() -> dict:
    now = datetime.now(timezone.utc)
    async with SessionLocal() as db:
        otp_result = await db.execute(delete(EmailOTP).where(EmailOTP.expires_at < now))
        token_result = await db.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
        await db.commit()
        return {"otps_deleted": otp_result.rowcount, "refresh_tokens_deleted": token_result.rowcount}


@celery_app.task(name="app.services.users.maintenance_service.cleanup_expired_data")
def cleanup_expired_data() -> dict:
    """Celery-beat daily job: purge expired OTPs and expired refresh token rows."""
    return asyncio.run(_cleanup())
