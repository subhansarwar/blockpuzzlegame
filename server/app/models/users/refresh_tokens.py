import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    device_info: Mapped[str | None] = mapped_column(String(255))  # e.g. "iOS 17 / iPhone 15"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
