from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ProjectCreate(BaseModel):
    topic: str
    settings: Optional[Dict[str, Any]] = {}


class ProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    topic: str
    status: str
    settings_json: Optional[Dict[str, Any]] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
