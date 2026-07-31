# app/models/game/stats.py
import uuid
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserGameStats(Base):
    __tablename__ = "user_game_stats"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    all_time_high_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_combo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_lines_cleared: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Points: the one real spendable currency (Levels + Daily Challenges + ad rewards; spent in Shop)
    points_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # lifetime earned, never decreases

    # Coins: earned only via Daily Challenges, used for the Arena "coins" ranking (not spendable)
    coins_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_coins_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="game_stats")
