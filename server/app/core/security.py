# core/security.py
import secrets
import uuid
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        pw_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


def generate_otp_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(settings.OTP_LENGTH))


def _create_token(user_id: str, *, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    exp = now + expires_delta
    jti = str(uuid.uuid4())
    to_encode = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": exp,
        "jti": jti,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti, exp


def create_access_token(user_id: str) -> str:
    token, _, _ = _create_token(
        user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return token


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at) — caller persists jti/expiry in the refresh_tokens table."""
    return _create_token(
        user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


_BLOCKLIST_PREFIX = "auth:blocklist:jti:"


async def blocklist_token(jti: str, expires_at: datetime) -> None:
    """Revoke a token immediately (logout) by blocking its jti until it would have expired anyway."""
    ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    if ttl > 0:
        await redis_client.set(f"{_BLOCKLIST_PREFIX}{jti}", "1", ex=ttl)


async def is_token_blocklisted(jti: str) -> bool:
    return bool(await redis_client.exists(f"{_BLOCKLIST_PREFIX}{jti}"))