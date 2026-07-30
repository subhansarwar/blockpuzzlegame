# app/models/social/achievement.py
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AchievementDefinition(Base):
    """Static catalog of badges, e.g. category='combo_kings' has 20 tiers by lifetime points."""
    __tablename__ = "achievement_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    tier: Mapped[int] = mapped_column(Integer)  # 1..N within its category
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500))
    icon_url: Mapped[str | None] = mapped_column(String(500))
    points_threshold: Mapped[int] = mapped_column(Integer)  # lifetime total_points required to unlock
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_links = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


class UserAchievement(Base):
    """Existence of a row = claimed. Unclaimed-but-unlocked progress is computed on the fly."""
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    achievement_id: Mapped[int] = mapped_column(
        ForeignKey("achievement_definitions.id", ondelete="CASCADE"), nullable=False
    )
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="achievements")
    achievement = relationship("AchievementDefinition", back_populates="user_links")
