from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class AdminMetrics(BaseModel):
    total_users: int
    new_users_7d: int
    active_subscriptions: int
    videos_today: int
    videos_this_month: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    subscription_plan: Optional[str] = None
    video_count: int = 0

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    name: Optional[str] = None


class AdminJobResponse(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    status: str
    progress_pct: int
    celery_task_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    user_email: Optional[str] = None
    topic: Optional[str] = None

    class Config:
        from_attributes = True


class SystemSettingResponse(BaseModel):
    key: str
    value: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemSettingUpdate(BaseModel):
    value: str


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    admin_id: Optional[uuid.UUID] = None
    action: str
    target: Optional[str] = None
    created_at: datetime
    admin_email: Optional[str] = None

    class Config:
        from_attributes = True
