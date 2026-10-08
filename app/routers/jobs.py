import uuid

from arq.connections import ArqRedis, create_pool, RedisSettings
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.enums import JobStatus, JobType
from app.models.job import Job
from app.models.job_event import JobEvent
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.job import JobCreate, JobEventResponse, JobResponse
from app.schemas.job import JobListResponse
from app.core.rate_limit import rate_limit_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def get_arq_pool() -> ArqRedis:
    pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        yield pool
    finally:
        await pool.close()


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit_jobs)])
async def create_job(
    data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    arq: ArqRedis = Depends(get_arq_pool),
):
    # Validate payload shape per job type — fail fast, before queueing
    if data.type == JobType.TEXT_ANALYZE and "text" not in data.payload:
        raise HTTPException(422, "payload.text is required for text_analyze")

    job = Job(user_id=current_user.id, type=data.type, payload=data.payload)
    db.add(job)
    await db.flush()  # get job.id

    db.add(JobEvent(job_id=job.id, to_status=JobStatus.QUEUED, message="Job submitted"))
    await db.commit()

    await arq.enqueue_job("process_job", str(job.id))

    await db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job


@router.get("/{job_id}/events", response_model=list[JobEventResponse])
async def get_job_events(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    result = await db.execute(
        select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at)
    )
    return result.scalars().all()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(Job).where(Job.user_id == current_user.id)
    total = await db.scalar(
        select(func.count()).select_from(base.subquery())
    )
    result = await db.execute(
        base.order_by(Job.created_at.desc()).offset(skip).limit(limit)
    )
    return JobListResponse(
        items=result.scalars().all(), total=total, skip=skip, limit=limit
    )