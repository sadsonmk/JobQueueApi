from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=['health'])

async def get_redis():
    client = redis.from_url(settings.REDIS_URL)
    try:
        yield client
    finally:
        await client.aclose()


@router.get('/health')
async def health(db: AsyncSession = Depends(get_db), redis_client: redis.Redis = Depends(get_redis)):
    await db.execute(text("SELECT 1"))
    await redis_client.ping()
    return {"status": "OK", "db": "OK", "redis": "OK"}