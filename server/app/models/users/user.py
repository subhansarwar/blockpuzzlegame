# app/models/users/user.py
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- account / auth ---
    providers = relationship("AuthProvider", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")

    # --- gameplay ---
    game_stats = relationship("UserGameStats", back_populates="user", uselist=False, cascade="all, delete-orphan")
    game_sessions = relationship("GameSession", back_populates="user", cascade="all, delete-orphan")
    time_attack_best = relationship("TimeAttackBest", back_populates="user", uselist=False, cascade="all, delete-orphan")
    classic_bests = relationship("ClassicBest", back_populates="user", cascade="all, delete-orphan")
    level_state = relationship("UserLevelState", back_populates="user", uselist=False, cascade="all, delete-orphan")
    level_progress = relationship("LevelProgress", back_populates="user", cascade="all, delete-orphan")
    daily_challenge_claims = relationship("DailyChallengeClaim", back_populates="user", cascade="all, delete-orphan")

    # --- social / competitive ---
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    weekly_scores = relationship("WeeklyScore", back_populates="user", cascade="all, delete-orphan")

    # --- shop ---
    purchases = relationship("UserPurchase", back_populates="user", cascade="all, delete-orphan")
    ad_reward_logs = relationship("AdRewardLog", back_populates="user", cascade="all, delete-orphan")
