import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    topic: str
    settings: dict[str, Any] | None = {}


class ProjectUpdate(BaseModel):
    topic: str | None = None
    settings: dict[str, Any] | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    topic: str
    status: str
    settings_json: dict[str, Any] | None = {}
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
