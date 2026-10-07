import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.job_event import JobEvent


async def record_event(
    db: AsyncSession, job_id: uuid.UUID,
    to_status: JobStatus, from_status: JobStatus | None = None,
    message: str | None = None,
) -> None:
    db.add(JobEvent(job_id=job_id, from_status=from_status,
                    to_status=to_status, message=message))
    await db.flush()