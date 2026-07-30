# app/models/game/game_session.py
import enum
import uuid
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class GameMode(str, enum.Enum):
    time_attack = "time_attack"
    classic = "classic"
    levels = "levels"
    daily_challenge = "daily_challenge"


class Difficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class GameSession(Base):
    """Immutable log of every completed play session across all game modes. Feeds stats/leaderboards."""
    __tablename__ = "game_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    mode: Mapped[GameMode] = mapped_column(SAEnum(GameMode, name="game_mode"), nullable=False, index=True)
    difficulty: Mapped[Difficulty | None] = mapped_column(SAEnum(Difficulty, name="game_difficulty"), nullable=True)
    level_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_number: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-7 daily challenge cycle day

    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_combo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lines_cleared: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ads_watched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # time-attack extension ads

    coins_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="game_sessions")
