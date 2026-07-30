# app/models/users/preferences.py
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    sound_effect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    haptic_feedback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")
