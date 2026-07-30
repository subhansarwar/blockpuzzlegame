# app/services/users/auth_service.py
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    blocklist_token,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.google_auth import verify_google_token
from app.core.apple_auth import verify_apple_token
from app.models.users.user import User
from app.models.users.auth_provider import AuthProvider
from app.models.users.refresh_tokens import RefreshToken
from app.models.users.preferences import UserPreference
from app.models.game.stats import UserGameStats
from app.models.game.levels import UserLevelState
from app.models.game.time_attack import TimeAttackBest
from app.schemas.users.auth import (
    AppleOAuthRequest,
    EmailLoginRequest,
    EmailSignupRequest,
    ForgotPasswordRequest,
    GoogleOAuthRequest,
    MessageResponse,
    OTPSentResponse,
    RefreshTokenRequest,
    ResendOTPRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyOTPRequest,
)
from app.services.users import audit_service, otp_service

_USERNAME_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9_]")


async def _is_username_taken(db: AsyncSession, username: str) -> bool:
    result = await db.execute(select(User.id).where(User.username == username))
    return result.scalar_one_or_none() is not None


async def generate_username(db: AsyncSession, seed: str) -> str:
    base = _USERNAME_SANITIZE_RE.sub("", seed.split("@")[0]).lower()
    if len(base) < 3:
        base = f"player{base}"
    base = base[:24] or "player"

    candidate = base
    suffix = 0
    while await _is_username_taken(db, candidate):
        suffix += 1
        candidate = f"{base}{suffix}"[:30]
    return candidate


async def provision_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    name: str | None,
    avatar_url: str | None,
    hashed_password: str | None,
    is_verified: bool,
) -> User:
    user = User(
        email=email,
        username=username,
        name=name,
        avatar_url=avatar_url,
        hashed_password=hashed_password,
        is_verified=is_verified,
    )
    db.add(user)
    await db.flush()  # populate user.id for the dependent rows below

    db.add(UserPreference(user_id=user.id))
    db.add(UserGameStats(user_id=user.id))
    db.add(UserLevelState(user_id=user.id))
    db.add(TimeAttackBest(user_id=user.id))
    await db.flush()
    return user


async def _issue_token_pair(db: AsyncSession, user: User, device_info: str | None) -> tuple[str, str]:
    access_token = create_access_token(str(user.id))
    refresh_token, jti, expires_at = create_refresh_token(str(user.id))
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at, device_info=device_info))
    await db.flush()
    return access_token, refresh_token


async def _get_or_link_oauth_user(
    db: AsyncSession,
    *,
    provider: str,
    sub: str,
    email: str | None,
    name: str | None,
    avatar_url: str | None,
) -> User:
    result = await db.execute(
        select(AuthProvider).where(AuthProvider.provider == provider, AuthProvider.provider_user_id == sub)
    )
    ap = result.scalar_one_or_none()
    if ap:
        result = await db.execute(select(User).where(User.id == ap.user_id))
        return result.scalar_one()

    user = None
    if email:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user:
        db.add(AuthProvider(user_id=user.id, provider=provider, provider_user_id=sub, email=email, name=name, avatar_url=avatar_url))
        await db.flush()
        return user

    if not email:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"{provider.title()} did not share an email; please try again or use another sign-in method",
        )

    username = await generate_username(db, name or email)
    name = await generate_username(db, name or email)
    user = await provision_user(
        db,
        email=email,
        username=username,
        name=name,
        avatar_url=avatar_url,
        hashed_password=None,
        is_verified=True,
    )
    db.add(AuthProvider(user_id=user.id, provider=provider, provider_user_id=sub, email=email, name=name, avatar_url=avatar_url))
    await db.flush()
    return user


async def signup_email(db: AsyncSession, req: EmailSignupRequest, *, ip: str | None, ua: str | None) -> OTPSentResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    existing = result.scalar_one_or_none()

    if existing:
        if existing.is_verified:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="An account with this email already exists")
        existing.hashed_password = hash_password(req.password)
        await db.flush()
        await otp_service.issue_otp(db, req.email, purpose="verify")
        await audit_service.log_event(
            db, user_id=existing.id, event="signup", provider="email", status="success",
            detail="resend for unverified account", ip_address=ip, user_agent=ua,
        )
        await db.commit()
        return OTPSentResponse(message="Verification code sent", email=req.email)

    username = await generate_username(db, req.email)
    name = await generate_username(db, req.email)
    user = await provision_user(
        db, email=req.email, username=username, name=name, avatar_url=None,
        hashed_password=hash_password(req.password), is_verified=False,
    )
    db.add(AuthProvider(user_id=user.id, provider="email", provider_user_id=req.email, email=req.email))
    await otp_service.issue_otp(db, req.email, purpose="verify")
    await audit_service.log_event(db, user_id=user.id, event="signup", provider="email", status="success", ip_address=ip, user_agent=ua)
    await db.commit()
    return OTPSentResponse(message="Verification code sent", email=req.email)


async def resend_otp(db: AsyncSession, req: ResendOTPRequest, *, ip: str | None, ua: str | None) -> OTPSentResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")
    if user.is_verified:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Account already verified")

    await otp_service.issue_otp(db, req.email, purpose="verify")
    await audit_service.log_event(db, user_id=user.id, event="resend_otp", provider="email", status="success", ip_address=ip, user_agent=ua)
    await db.commit()
    return OTPSentResponse(message="Verification code sent", email=req.email)


async def verify_signup_otp(db: AsyncSession, req: VerifyOTPRequest, *, ip: str | None, ua: str | None) -> TokenResponse:
    await otp_service.verify_otp(db, req.email, req.otp)

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    user.is_verified = True
    user.last_login_at = datetime.now(timezone.utc)
    access_token, refresh_token = await _issue_token_pair(db, user, None)
    await audit_service.log_event(db, user_id=user.id, event="verify_otp", provider="email", status="success", ip_address=ip, user_agent=ua)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserResponse.model_validate(user))


async def login_email(db: AsyncSession, req: EmailLoginRequest, *, ip: str | None, ua: str | None) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        await audit_service.log_event(
            db, user_id=user.id if user else None, event="login_failed", provider="email",
            status="failure", detail="invalid credentials", ip_address=ip, user_agent=ua,
        )
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account is temporarily locked, try again later")

    if not verify_password(req.password, user.hashed_password):
        user.failed_login_attempts += 1
        locked = False
        if user.failed_login_attempts >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            locked = True
        await audit_service.log_event(
            db, user_id=user.id, event="account_locked" if locked else "login_failed", provider="email",
            status="failure", ip_address=ip, user_agent=ua,
        )
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account not verified")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    access_token, refresh_token = await _issue_token_pair(db, user, req.device_info)
    await audit_service.log_event(db, user_id=user.id, event="login_email", provider="email", status="success", ip_address=ip, user_agent=ua)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserResponse.model_validate(user))


async def login_google(db: AsyncSession, req: GoogleOAuthRequest, *, ip: str | None, ua: str | None) -> TokenResponse:
    claims = await verify_google_token(req.id_token)
    user = await _get_or_link_oauth_user(
        db, provider="google", sub=claims["sub"], email=claims.get("email"),
        name=claims.get("name"), avatar_url=claims.get("picture"),
    )
    user.last_login_at = datetime.now(timezone.utc)
    access_token, refresh_token = await _issue_token_pair(db, user, req.device_info)
    await audit_service.log_event(db, user_id=user.id, event="login_google", provider="google", status="success", ip_address=ip, user_agent=ua)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserResponse.model_validate(user))


async def login_apple(db: AsyncSession, req: AppleOAuthRequest, *, ip: str | None, ua: str | None) -> TokenResponse:
    claims = await verify_apple_token(req.identity_token)
    user = await _get_or_link_oauth_user(
        db, provider="apple", sub=claims["sub"], email=claims.get("email"),
        name=req.full_name, avatar_url=None,
    )
    user.last_login_at = datetime.now(timezone.utc)
    access_token, refresh_token = await _issue_token_pair(db, user, req.device_info)
    await audit_service.log_event(db, user_id=user.id, event="login_apple", provider="apple", status="success", ip_address=ip, user_agent=ua)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=UserResponse.model_validate(user))


async def refresh_tokens(db: AsyncSession, req: RefreshTokenRequest) -> TokenResponse:
    try:
        payload = jwt.decode(req.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("wrong token type")
        jti = payload["jti"]
        user_id = UUID(str(payload["sub"]))
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    stored = result.scalar_one_or_none()
    if not stored or stored.is_revoked or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired")

    stored.is_revoked = True  # rotate — one-time use

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Account is unavailable")

    access_token, new_refresh_token = await _issue_token_pair(db, user, stored.device_info)
    await audit_service.log_event(db, user_id=user.id, event="token_refresh", status="success")
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token, user=UserResponse.model_validate(user))


async def logout(db: AsyncSession, user: User, access_payload: dict, refresh_token: str | None) -> MessageResponse:
    jti = access_payload.get("jti")
    exp = access_payload.get("exp")
    if jti and exp:
        await blocklist_token(jti, datetime.fromtimestamp(exp, tz=timezone.utc))

    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            result = await db.execute(select(RefreshToken).where(RefreshToken.jti == payload.get("jti")))
            stored = result.scalar_one_or_none()
            if stored:
                stored.is_revoked = True
        except JWTError:
            pass

    await audit_service.log_event(db, user_id=user.id, event="logout", status="success")
    await db.commit()
    return MessageResponse(message="Logged out")


async def forgot_password(db: AsyncSession, req: ForgotPasswordRequest) -> OTPSentResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if user and user.hashed_password:
        await otp_service.issue_otp(db, req.email, purpose="reset")
        await db.commit()
    # Same response regardless of whether the account exists, to avoid leaking account existence
    return OTPSentResponse(message="If an account exists, a reset code has been sent", email=req.email)


async def reset_password(db: AsyncSession, req: ResetPasswordRequest) -> MessageResponse:
    await otp_service.verify_otp(db, req.email, req.otp)

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found")

    user.hashed_password = hash_password(req.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    await audit_service.log_event(db, user_id=user.id, event="password_reset", status="success")
    await db.commit()
    return MessageResponse(message="Password has been reset")

