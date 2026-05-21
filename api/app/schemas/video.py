from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class VideoGenerateRequest(BaseModel):
    project_id: uuid.UUID
    topic: str
    tone: Optional[str] = "engaging"
    style: Optional[str] = "informational"
    duration_seconds: Optional[int] = 60
    settings: Optional[Dict[str, Any]] = {}


class VideoJobResponse(BaseModel):
    id: uuid.UUID
    status: str
    progress_pct: int
    celery_task_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    storage_key: Optional[str] = None
    script_text: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    download_url: Optional[str] = None
    latest_job: Optional[VideoJobResponse] = None

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
