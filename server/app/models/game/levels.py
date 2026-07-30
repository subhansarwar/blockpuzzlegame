# app/models/game/levels.py
import uuid
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserLevelState(Base):
    """One row per user: current unlocked level + this mode's own score/best_score."""
    __tablename__ = "user_level_state"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    current_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # next level to play, 1-100
    best_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="level_state")


class LevelProgress(Base):
    """One row per (user, level) once that level has been completed."""
    __tablename__ = "level_progress"
    __table_args__ = (UniqueConstraint("user_id", "level_number", name="uq_level_progress_user_level"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level_number: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="level_progress")
