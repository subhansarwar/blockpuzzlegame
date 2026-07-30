# app/core/celery_app.py
import logging

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "block_game",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.services.users.email_service",
        "app.services.users.notification_service",
        "app.services.users.maintenance_service",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_default_retry_delay=30,
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-auth-data-daily": {
        "task": "app.services.users.maintenance_service.cleanup_expired_data",
        "schedule": crontab(hour=3, minute=0),
    },
}


def check_celery_workers(timeout: float = 1.0) -> bool:
    """Ping for live workers so we can warn loudly instead of silently dropping queued tasks (OTP emails, etc)."""
    try:
        pong = celery_app.control.inspect(timeout=timeout).ping()
    except Exception:
        pong = None
    if not pong:
        logger.warning(
            "No Celery workers responded to ping — tasks like OTP emails will be queued in Redis but never "
            "sent until a worker is running. Start one with: "
            "celery -A app.core.celery_app worker --loglevel=info -P solo"
        )
        return False
    return True
