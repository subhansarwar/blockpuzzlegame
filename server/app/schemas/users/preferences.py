# app/schemas/users/preferences.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class PreferenceUpdate(BaseModel):
    sound_effect: Optional[bool] = None
    haptic_feedback: Optional[bool] = None
    notifications_enabled: Optional[bool] = None


class PreferenceResponse(BaseModel):
    user_id: UUID
    sound_effect: bool
    haptic_feedback: bool
    notifications_enabled: bool

    class Config:
        from_attributes = True
