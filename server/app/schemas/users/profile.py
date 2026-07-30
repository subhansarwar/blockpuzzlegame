# app/schemas/users/profile.py
import re
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


class nameUpdateRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def valid_username(cls, v: str) -> str:
        if not _USERNAME_RE.match(v):
            raise ValueError("Name must be 3-30 characters: letters, numbers, underscore only")
        return v


class ProfileResponse(BaseModel):
    id: UUID
    username: str
    name: str | None
    email: str
    avatar_url: str | None
    linked_providers: list[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AvatarResponse(BaseModel):
    avatar_url: str | None

class ResetProgressResponse(BaseModel):
    message: str


class DeleteAccountRequest(BaseModel):
    password: str | None = None  # required to confirm for email/password accounts; ignored for OAuth-only accounts
