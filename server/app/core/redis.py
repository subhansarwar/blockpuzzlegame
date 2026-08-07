# app/core/redis.py
from typing import AsyncGenerator
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool
from app.core.config import settings

_pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
redis_client = Redis(connection_pool=_pool)


async def get_redis() -> AsyncGenerator[Redis, None]:
    yield redis_client


def rkey(*parts: str) -> str:
    """Namespace a Redis key with REDIS_KEY_PREFIX so this app's keys can't
    collide with other apps sharing the same Redis instance/DB."""
    return ":".join((settings.REDIS_KEY_PREFIX, *parts))
