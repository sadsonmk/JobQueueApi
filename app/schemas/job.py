import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import JobStatus, JobType


class JobCreate(BaseModel):
    type: JobType
    payload: dict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: JobType
    status: JobStatus
    result: dict | None
    error: str | None
    attempts: int
    max_attempts: int
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class JobEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: JobStatus | None
    to_status: JobStatus
    message: str | None
    created_at: datetime

class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    skip: int
    limit: int