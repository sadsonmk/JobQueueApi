import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
import asyncio
import contextlib


from app.main import app
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def user():
    email = f"user-{uuid.uuid4().hex[:10]}@test.com"   # unique per run
    async with AsyncSessionLocal() as db:
        u = User(email=email, hashed_password=hash_password("secret123"))
        db.add(u)
        await db.commit()
        await db.refresh(u)
        yield u
        # teardown: remove what this test created (cascade cleans jobs/events)
        await db.execute(delete(User).where(User.id == u.id))
        await db.commit()


@pytest_asyncio.fixture
async def auth_client(client, user):
    resp = await client.post("/auth/login", json={
        "email": user.email, "password": "secret123",
    })
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client

@pytest_asyncio.fixture(scope="session")
async def worker():
    """Run the real arq worker in-process for the whole test session."""
    from arq.worker import run_worker
    from app.workers.worker import WorkerSettings

    task = asyncio.create_task(run_worker(WorkerSettings))
    await asyncio.sleep(1)          # give it a moment to connect to Redis
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task