# app/services/users/audit_service.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users.audit_logs import AuditLog


async def log_event(
    db: AsyncSession,
    *,
    user_id: UUID | None,
    event: str,
    provider: str | None = None,
    status: str = "success",
    detail: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        event=event,
        provider=provider,
        status=status,
        detail=detail,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry
