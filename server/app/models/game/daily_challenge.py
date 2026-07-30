# app/models/game/daily_challenge.py
import uuid
from datetime import date, datetime
from sqlalchemy import Integer, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DailyChallengeClaim(Base):
    """One row per (user, calendar date) once that day's challenge reward has been claimed."""
    __tablename__ = "daily_challenge_claims"
    __table_args__ = (UniqueConstraint("user_id", "challenge_date", name="uq_daily_challenge_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # UTC calendar date
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-7 within the weekly cycle
    best_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coins_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="daily_challenge_claims")
