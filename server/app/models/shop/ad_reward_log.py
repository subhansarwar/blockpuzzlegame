# app/models/shop/ad_reward_log.py
import enum
import uuid
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AdRewardContext(str, enum.Enum):
    shop_points = "shop_points"          # Shop: watch ad -> +100 points, max 10/day
    time_attack_extend = "time_attack_extend"  # Time Attack: watch ad -> extend session time limit


class AdRewardLog(Base):
    """Every rewarded-ad completion the client reported. Backs daily rate limiting + audit history."""
    __tablename__ = "ad_reward_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    context: Mapped[AdRewardContext] = mapped_column(SAEnum(AdRewardContext, name="ad_reward_context"), nullable=False)
    reward_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="ad_reward_logs")
