import asyncio

from sqlalchemy import select

from app.models.enums import JobStatus
from app.models.job import Job
from httpx import ASGITransport, AsyncClient
from app.main import app


async def test_submit_job_returns_202(auth_client):
    resp = await auth_client.post("/jobs", json={
        "type": "text_analyze",
        "payload": {"text": "hello world hello"},
    })
    assert resp.status_code == 202
    assert resp.json()["status"] == JobStatus.QUEUED.value


async def test_cannot_see_other_users_job(auth_client, user):
    resp = await auth_client.post("/jobs", json={
        "type": "text_analyze", "payload": {"text": "hi"}})
    job_id = resp.json()["id"]

    # A brand-new client with no auth headers — a real stranger
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as stranger:
        r = await stranger.get(f"/jobs/{job_id}")
    assert r.status_code in (401, 403, 404)


async def test_worker_processes_job(auth_client):
    resp = await auth_client.post("/jobs", json={
        "type": "text_analyze",
        "payload": {"text": "one two three two"},
    })
    job_id = resp.json()["id"]

    # Poll until the worker finishes (Upstash/local Redis must be running)
    for _ in range(20):
        await asyncio.sleep(0.5)
        status_resp = await auth_client.get(f"/jobs/{job_id}")
        status = status_resp.json()["status"]
        if status in (JobStatus.SUCCEEDED.value, JobStatus.FAILED.value):
            break

    assert status == JobStatus.SUCCEEDED.value
    assert status_resp.json()["result"]["word_count"] == 4

    events = (await auth_client.get(f"/jobs/{job_id}/events")).json()
    transitions = [e["to_status"] for e in events]
    assert transitions == ["queued", "running", "succeeded"]