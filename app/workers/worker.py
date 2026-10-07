import uuid
from datetime import datetime, timezone

from arq.connections import RedisSettings
from arq import cron
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.enums import JobStatus, JobType
from app.models.job import Job
from app.services.job_service import record_event


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def process_text(payload: dict) -> dict:
    """Deterministic text analysis — testable, no external calls."""
    text = payload["text"]
    words = text.lower().split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "top_words": sorted(set(words), key=words.count, reverse=True)[:5],
    }


async def process_job(ctx, job_id: str) -> None:
    """arq entrypoint: runs in the worker process, not the API."""
    job_uuid = uuid.UUID(job_id)

    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_uuid)
        if job is None or job.status != JobStatus.QUEUED:
            return  # already processed or cancelled — idempotent

        job.status = JobStatus.RUNNING
        job.started_at = utcnow()
        job.attempts += 1
        await record_event(db, job_uuid, JobStatus.RUNNING, JobStatus.QUEUED,message=f"Attempt {job.attempts}")
        await db.commit()

        try:
            if job.type == JobType.TEXT_ANALYZE:
                result = await process_text(job.payload)
            else:
                raise ValueError(f"Unknown job type: {job.type}")

            job.status = JobStatus.SUCCEEDED
            job.result = result
            job.finished_at = utcnow()
            job.error = None
            await record_event(db, job_uuid, JobStatus.SUCCEEDED, JobStatus.RUNNING)
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            job.finished_at = utcnow()
            await record_event(db, job_uuid, JobStatus.FAILED, JobStatus.RUNNING,message=str(exc))
            raise  # let arq handle retries

        await db.commit()


class WorkerSettings:
    functions = [process_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 300
    max_tries = 3