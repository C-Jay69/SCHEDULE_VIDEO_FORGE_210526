from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.security import get_current_user
from ..database import get_db
from ..models.plan import Plan
from ..models.project import Project
from ..models.published_post import PublishedPost
from ..models.schedule import Schedule, ScheduleStatus
from ..models.social_account import SocialAccount
from ..models.subscription import Subscription
from ..models.usage import UsageEvent
from ..models.user import User, UserRole
from ..models.video import Video
from ..models.video_job import JobStatus, VideoJob
from ..schemas.auth import UserUpdate
from ..schemas.users import (
    DashboardStats,
    SocialAccountResponse,
    UsageSummary,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse.model_validate(current_user)


@router.put("/me", response_model=UserProfileResponse)
@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.name is not None:
        current_user.name = data.name
    if data.email is not None and data.email != current_user.email:
        existing = db.query(User).filter(User.email == data.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = data.email
    db.commit()
    db.refresh(current_user)
    return UserProfileResponse.model_validate(current_user)


@router.get("/me/usage", response_model=UsageSummary)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan = db.query(Plan).filter(Plan.name == (sub.plan_name if sub else "starter")).first()

    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    videos_generated = (
        db.query(Video).filter(Video.user_id == current_user.id, Video.created_at >= start_of_month).count()
    )
    motion_credits_used = (
        db.query(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .filter(UsageEvent.user_id == current_user.id, UsageEvent.event_type == "motion_credit_usage")
        .scalar()
    ) or 0

    storage_used_mb = 0
    videos_total = db.query(Video).filter(Video.user_id == current_user.id).count()
    # Rough estimate: assume ~5MB per generated video file.
    storage_used_mb = videos_total * 5

    is_admin = current_user.role == UserRole.admin
    return UsageSummary(
        videos_generated=videos_generated,
        videos_limit=-1 if is_admin else (plan.video_limit_monthly if plan else 3),
        storage_used_mb=storage_used_mb,
        storage_limit_mb=-1 if is_admin else ((plan.storage_limit_gb * 1024) if plan else 1024),
        motion_credits_used=motion_credits_used,
        motion_credits_limit=-1 if is_admin else (plan.motion_credits_monthly if plan else 0),
    )


@router.get("/me/social-accounts", response_model=list[SocialAccountResponse])
async def get_social_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == current_user.id).all()
    return [SocialAccountResponse.model_validate(a) for a in accounts]


@router.delete("/me/social-accounts/{platform}")
async def disconnect_social_account(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = (
        db.query(SocialAccount)
        .filter(SocialAccount.user_id == current_user.id, SocialAccount.platform == platform)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not connected")
    db.delete(account)
    db.commit()
    return {"message": f"{platform} disconnected"}


@router.get("/me/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan_name = sub.plan_name if sub else "starter"
    plan = db.query(Plan).filter(Plan.name == plan_name).first()

    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    videos_generated = (
        db.query(Video).filter(Video.user_id == current_user.id, Video.created_at >= start_of_month).count()
    )
    scheduled_posts = (
        db.query(Schedule)
        .filter(Schedule.user_id == current_user.id, Schedule.status == ScheduleStatus.pending)
        .count()
    )
    published_posts = (
        db.query(PublishedPost)
        .filter(PublishedPost.video_id.in_(db.query(Video.id).filter(Video.user_id == current_user.id)))
        .count()
    )
    failed_jobs = (
        db.query(VideoJob)
        .join(Video, VideoJob.video_id == Video.id)
        .filter(Video.user_id == current_user.id, VideoJob.status == JobStatus.failed)
        .count()
    )

    projects = (
        db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).limit(5).all()
    )
    recent_projects = []
    for p in projects:
        video_count = db.query(Video).filter(Video.project_id == p.id).count()
        latest_video = db.query(Video).filter(Video.project_id == p.id).order_by(Video.created_at.desc()).first()
        recent_projects.append(
            {
                "id": str(p.id),
                "title": p.topic,
                "status": latest_video.status.value if latest_video else p.status.value,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "video_count": video_count,
            }
        )

    return DashboardStats(
        videos_generated=videos_generated,
        videos_limit=-1 if current_user.role == UserRole.admin else (plan.video_limit_monthly if plan else 3),
        scheduled_posts=scheduled_posts,
        published_posts=published_posts,
        failed_jobs=failed_jobs,
        plan_name=plan_name,
        plan_status=sub.status.value if sub else "active",
        recent_projects=recent_projects,
    )
