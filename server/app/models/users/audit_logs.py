import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AuditLog(Base):
    """Immutable record of every auth event for security and compliance."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Event types: signup, verify_otp, resend_otp, login_email, login_google, login_apple,
    #              login_failed, account_locked, token_refresh, logout, password_reset,
    #              profile_update, avatar_update, reset_progress, delete_account,
    #              shop_purchase, ad_reward, achievement_claim
    event: Mapped[str] = mapped_column(String(50), index=True)
    provider: Mapped[str | None] = mapped_column(String(50))  # email / google / apple
    status: Mapped[str] = mapped_column(String(20))           # success / failure
    detail: Mapped[str | None] = mapped_column(Text)          # extra context (error reason, etc.)

    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="audit_logs")
