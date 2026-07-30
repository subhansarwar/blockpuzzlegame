# app/services/users/email_service.py
import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())


@celery_app.task(name="app.services.users.email_service.send_otp_email", bind=True, max_retries=3)
def send_otp_email(self, to_email: str, otp_code: str, purpose: str = "verify") -> None:
    subject = (
        "Your BLOCK PUZZLE verification code"
        if purpose == "verify"
        else "Your BLOCK PUZZLE password reset code"
    )
    body = (
        f"Your OTP code is: {otp_code}\n"
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
        f"If you didn't request this, you can safely ignore this email."
    )
    try:
        _send_email_sync(to_email, subject, body)
        logger.info("Sent %s OTP email to %s", purpose, to_email)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            logger.error("Giving up on %s OTP email to %s after %d retries: %s", purpose, to_email, self.request.retries, exc)
            raise
        raise self.retry(exc=exc, countdown=10)
