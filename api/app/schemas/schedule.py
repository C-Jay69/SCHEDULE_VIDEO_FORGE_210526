from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class ScheduleCreate(BaseModel):
    video_id: uuid.UUID
    platform: str
    scheduled_at: datetime


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
    items: List[ScheduleResponse]
    total: int
