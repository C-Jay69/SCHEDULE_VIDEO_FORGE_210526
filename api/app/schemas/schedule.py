import uuid
from datetime import datetime

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    video_id: uuid.UUID
    platform: str
    scheduled_at: datetime


class ScheduleUpdate(BaseModel):
    platform: str | None = None
    scheduled_at: datetime | None = None


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    user_id: uuid.UUID
    platform: str
    scheduled_at: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]
    total: int
