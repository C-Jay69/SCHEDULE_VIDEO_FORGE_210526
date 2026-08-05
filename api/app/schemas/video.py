import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class VideoGenerateRequest(BaseModel):
    project_id: uuid.UUID
    topic: str
    tone: str | None = "engaging"
    style: str | None = "informational"
    duration_seconds: int | None = 60
    settings: dict[str, Any] | None = {}


class VideoJobResponse(BaseModel):
    id: uuid.UUID
    status: str
    progress_pct: int
    celery_task_id: str | None = None
    error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    storage_key: str | None = None
    script_text: str | None = None
    error_message: str | None = None
    created_at: datetime
    download_url: str | None = None
    latest_job: VideoJobResponse | None = None
    # Convenience fields for the frontend detail/editor pages.
    title: str | None = None
    platform: str | None = None
    format: str | None = None
    duration: str | None = None
    stream_url: str | None = None
    schedule: dict | None = None

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    items: list[VideoResponse]
    total: int
