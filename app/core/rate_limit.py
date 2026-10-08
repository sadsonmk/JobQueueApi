from fastapi import Depends, HTTPException, status
import redis.asyncio as redis

from app.core.config import settings
from app.models.user import User
from app.routers.auth import get_current_user

LIMIT = 20          # requests
WINDOW = 60         # seconds


async def rate_limit_jobs(
    current_user: User = Depends(get_current_user),
):
    key = f"ratelimit:jobs:{current_user.id}"
    client = redis.from_url(settings.REDIS_URL)
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, WINDOW)
        if count > LIMIT:
            ttl = await client.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry in {ttl} seconds.",
                headers={"Retry-After": str(ttl)},
            )
    finally:
        await client.aclose()