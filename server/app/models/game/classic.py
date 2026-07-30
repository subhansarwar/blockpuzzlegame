# app/models/game/classic.py
import uuid
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.game.game_session import Difficulty


class ClassicBest(Base):
    __tablename__ = "classic_best"
    __table_args__ = (UniqueConstraint("user_id", "difficulty", name="uq_classic_best_user_difficulty"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    difficulty: Mapped[Difficulty] = mapped_column(SAEnum(Difficulty, name="game_difficulty"), nullable=False)
    best_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="classic_bests")
