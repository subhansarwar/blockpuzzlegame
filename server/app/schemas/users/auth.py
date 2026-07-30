# app/schemas/users/auth.py
from pydantic import BaseModel, EmailStr, field_validator, field_serializer
from uuid import UUID
from datetime import datetime


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return email
    visible = local[:2]
    return f"{visible}{'*' * max(len(local) - len(visible), 3)}@{domain}"


# ============= Request schemas =======================
class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_info: str | None = None


class GoogleOAuthRequest(BaseModel):
    """Mobile app sends the Google ID token; backend verifies it server-side."""
    id_token: str
    device_info: str | None = None


class AppleOAuthRequest(BaseModel):
    """Mobile app sends the Apple identity token; backend verifies it server-side."""
    identity_token: str
    authorization_code: str
    full_name: str | None = None   # only provided on first sign-in
    device_info: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ============= Response schemas=======================
class UserResponse(BaseModel):
    id: UUID
    username: str
    name: str | None
    email: str
    avatar_url: str | None
    is_verified: bool
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class OTPSentResponse(BaseModel):
    message: str
    email: str

    @field_serializer("email")
    def serialize_email(self, email: str) -> str:
        return mask_email(email)


class MessageResponse(BaseModel):
    message: str
