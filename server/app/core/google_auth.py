# app/core/google_auth.py
import asyncio
from functools import partial

from fastapi import HTTPException, status
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings

def _verify_sync(token: str) -> dict:
    """Blocking call — runs in a thread pool so it doesn't block the event loop."""
    try:
        idinfo = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Google token: {exc}")

    if not idinfo.get("email_verified", False):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Google account email is not verified")

    return {
        "sub": idinfo["sub"],
        "email": idinfo["email"],
        "name": idinfo.get("name"),
        "picture": idinfo.get("picture"),
    }

async def verify_google_token(id_token: str) -> dict:
    """Verify a Google ID token server-side and return the user claims."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google Sign-In is not configured")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_verify_sync, id_token))
