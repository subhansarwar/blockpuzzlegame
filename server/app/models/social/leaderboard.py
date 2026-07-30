# app/models/social/leaderboard.py
import uuid
from datetime import date, datetime
from sqlalchemy import Integer, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class WeeklyScore(Base):
    """Per-user, per-ISO-week accumulator that backs the Arena weekly leaderboard."""
    __tablename__ = "weekly_scores"
    __table_args__ = (UniqueConstraint("user_id", "week_start", name="uq_weekly_score_user_week"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # Monday (UTC) of the ISO week
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coins_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="weekly_scores")
