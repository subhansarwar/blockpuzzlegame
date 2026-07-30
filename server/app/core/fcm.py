import base64
import json
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings

logger = logging.getLogger(__name__)
_initialized = False

def init_fcm() -> None:
    global _initialized
    if _initialized or firebase_admin._apps:
        _initialized = True
        return
    try:
        decoded = base64.b64decode(settings.FIREBASE_SERVICE_ACCOUNT_BASE64).decode("utf-8")
        service_account = json.loads(decoded)
    except Exception as e:
        raise RuntimeError("Invalid FIREBASE_SERVICE_ACCOUNT_BASE64") from e
    cred = credentials.Certificate(service_account)
    firebase_admin.initialize_app(cred)
    _initialized = True


def send_multicast(tokens: list[str], *, title: str, body: str) -> list[str]:
    if not tokens:
        return []
    init_fcm()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens,
    )
    dead: list[str] = []
    try:
        resp = messaging.send_each_for_multicast(message)
        for tok, result in zip(tokens, resp.responses):
            if not result.success and isinstance(result.exception, messaging.UnregisteredError):
                dead.append(tok)
    except Exception:
        logger.exception("FCM multicast failed")
    return dead


def send_one(token: str, *, title: str, body: str) -> bool:
    init_fcm()
    try:
        messaging.send(messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
        ))
        return True
    except Exception:
        logger.exception("FCM send failed")
        return False