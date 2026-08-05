import uuid
from datetime import datetime

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    stripe_customer_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UsageSummary(BaseModel):
    videos_generated: int
    videos_limit: int
    storage_used_mb: int
    storage_limit_mb: int
    motion_credits_used: int
    motion_credits_limit: int


class SocialAccountResponse(BaseModel):
    id: uuid.UUID
    platform: str
    account_name: str | None = None
    is_active: bool = True
    expires_at: datetime | None = None
    connected_at: datetime | None = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    videos_generated: int
    videos_limit: int
    scheduled_posts: int
    published_posts: int
    failed_jobs: int
    plan_name: str
    plan_status: str
    recent_projects: list[dict]


class PublishedPostResponse(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    platform: str
    platform_url: str | None = None
    status: str
    published_at: datetime | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    id: int
    name: str
    category: str
    script_template: str
    title_template: str | None = None
    description_template: str | None = None
    hashtag_template: str | None = None
    is_default: bool

    class Config:
        from_attributes = True
