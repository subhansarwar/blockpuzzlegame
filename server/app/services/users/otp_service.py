# app/services/users/otp_service.py
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import generate_otp_code, hash_password, verify_password
from app.models.users.otp import EmailOTP
from app.services.users.email_service import send_otp_email

_COOLDOWN_PREFIX = "otp:cooldown:"


async def _check_cooldown(email: str) -> None:
    key = f"{_COOLDOWN_PREFIX}{email}"
    ttl = await redis_client.ttl(key)
    if ttl and ttl > 0:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {ttl}s before requesting another code",
        )


async def _set_cooldown(email: str) -> None:
    await redis_client.set(f"{_COOLDOWN_PREFIX}{email}", "1", ex=settings.OTP_RESEND_COOLDOWN_SECONDS)


async def issue_otp(db: AsyncSession, email: str, *, purpose: str = "verify") -> None:
    await _check_cooldown(email)
    code = generate_otp_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    otp = EmailOTP(email=email, otp_code=hash_password(code), expires_at=expires_at)
    db.add(otp)
    await db.flush()
    await _set_cooldown(email)
    send_otp_email.delay(email, code, purpose)


async def verify_otp(db: AsyncSession, email: str, code: str) -> None:
    result = await db.execute(
        select(EmailOTP)
        .where(EmailOTP.email == email, EmailOTP.is_used == False)  # noqa: E712
        .order_by(EmailOTP.created_at.desc())
        .limit(1)
    )
    otp = result.scalar_one_or_none()
    if not otp:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No pending verification code for this email")
    if otp.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Verification code has expired")
    if otp.attempt_count >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts, request a new code")
    if not verify_password(code, otp.otp_code):
        otp.attempt_count += 1
        await db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")
    otp.is_used = True
    await db.flush()
