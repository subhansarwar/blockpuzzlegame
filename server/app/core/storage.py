# app/core/storage.py
import asyncio
import uuid
from functools import partial

from firebase_admin import storage as fb_storage

from app.core.config import settings
from app.core.fcm import init_fcm

_CONTENT_TYPE_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _bucket():
    init_fcm()
    return fb_storage.bucket(settings.FIREBASE_STORAGE_BUCKET)


def _upload_sync(user_id: str, content: bytes, content_type: str) -> str:
    ext = _CONTENT_TYPE_EXT.get(content_type, "bin")
    blob_path = f"avatars/{user_id}/{uuid.uuid4().hex}.{ext}"
    bucket = _bucket()
    blob = bucket.blob(blob_path)
    blob.upload_from_string(content, content_type=content_type)
    blob.make_public()
    return blob.public_url


def _delete_sync(avatar_url: str) -> None:
    bucket = _bucket()
    prefix = f"https://storage.googleapis.com/{bucket.name}/"
    if not avatar_url.startswith(prefix):
        return
    blob_path = avatar_url[len(prefix):]
    blob = bucket.blob(blob_path)
    if blob.exists():
        blob.delete()


async def upload_avatar(user_id: str, content: bytes, content_type: str) -> str:
    """Blocking Firebase Storage SDK call — runs in a thread pool so it doesn't block the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_upload_sync, user_id, content, content_type))


async def delete_avatar(avatar_url: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(_delete_sync, avatar_url))
