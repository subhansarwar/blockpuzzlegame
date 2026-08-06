# app/core/redis_client.py
from redis.asyncio import Redis
from app.core.config import settings

redis_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=5)

def rkey(*parts: str) -> str:
    """Build a Redis key namespaced with REDIS_KEY_PREFIX so it can't collide
    with keys from other backends sharing this Redis instance."""
    return ":".join((settings.REDIS_KEY_PREFIX, *parts))

async def check_redis_connection() -> bool:
    try:
        return await redis_client.ping()
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False
