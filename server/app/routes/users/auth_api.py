# app/routes/auth.py
from fastapi import APIRouter, Body, Request

from app.core.deps import CurrentTokenPayload, CurrentUser, SessionDep
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
    VerifyOTPRequest,
)
from app.services.users import auth_service

router = APIRouter(prefix="/auth", tags=["Authentications"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    return (request.client.host if request.client else None, request.headers.get("user-agent"))


@router.post("/signup", response_model=OTPSentResponse)
async def signup(req: EmailSignupRequest, request: Request, db: SessionDep):
    ip, ua = _client_meta(request)
    return await auth_service.signup_email(db, req, ip=ip, ua=ua)


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(req: VerifyOTPRequest, request: Request, db: SessionDep):
    ip, ua = _client_meta(request)
    return await auth_service.verify_signup_otp(db, req, ip=ip, ua=ua)


@router.post("/resend-otp", response_model=OTPSentResponse)
async def resend_otp(req: ResendOTPRequest, request: Request, db: SessionDep):
    ip, ua = _client_meta(request)
    return await auth_service.resend_otp(db, req, ip=ip, ua=ua)


@router.post("/login", response_model=TokenResponse)
async def login(req: EmailLoginRequest, request: Request, db: SessionDep):
    ip, ua = _client_meta(request)
    return await auth_service.login_email(db, req, ip=ip, ua=ua)


@router.post("/login/google", response_model=TokenResponse)
async def login_google(req: GoogleOAuthRequest, request: Request, db: SessionDep):
    ip, ua = _client_meta(request)
    return await auth_service.login_google(db, req, ip=ip, ua=ua)


@router.post("/login/apple", response_model=TokenResponse)
async def login_apple(req: AppleOAuthRequest, request: Request, db: SessionDep):
    ip, ua = _client_meta(request)
    return await auth_service.login_apple(db, req, ip=ip, ua=ua)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshTokenRequest, db: SessionDep):
    return await auth_service.refresh_tokens(db, req)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    db: SessionDep,
    user: CurrentUser,
    payload: CurrentTokenPayload,
    req: RefreshTokenRequest | None = Body(default=None),
):
    return await auth_service.logout(db, user, payload, req.refresh_token if req else None)


@router.post("/forgot-password", response_model=OTPSentResponse)
async def forgot_password(req: ForgotPasswordRequest, db: SessionDep):
    return await auth_service.forgot_password(db, req)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(req: ResetPasswordRequest, db: SessionDep):
    return await auth_service.reset_password(db, req)
