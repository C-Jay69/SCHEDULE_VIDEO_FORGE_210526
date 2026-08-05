import uuid
from datetime import datetime

from pydantic import BaseModel


class AdminMetrics(BaseModel):
    total_users: int
    new_users_7d: int
    active_subscriptions: int
    active_users: int = 0
    videos_today: int
    videos_this_month: int
    total_videos: int = 0
    total_schedules: int = 0
    total_published: int = 0
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    mrr_cents: int = 0
    storage_used_mb: int = 0
    published_by_platform: dict = {}


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    stripe_customer_id: str | None = None
    created_at: datetime
    subscription_plan: str | None = None
    video_count: int = 0

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    role: str | None = None
    name: str | None = None


class AdminJobResponse(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    status: str
    progress_pct: int
    celery_task_id: str | None = None
    error: str | None = None
    created_at: datetime
    user_email: str | None = None
    topic: str | None = None

    class Config:
        from_attributes = True


class SystemSettingResponse(BaseModel):
    key: str
    id: str | None = None
    value: str | None = None
    description: str | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SystemSettingCreate(BaseModel):
    key: str
    value: str | None = None
    description: str | None = None


class SystemSettingUpdate(BaseModel):
    value: str | None = None
    description: str | None = None


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    admin_id: uuid.UUID | None = None
    action: str
    target: str | None = None
    created_at: datetime
    admin_email: str | None = None

    class Config:
        from_attributes = True
