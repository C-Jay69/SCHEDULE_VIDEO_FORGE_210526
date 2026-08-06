import contextlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..core.security import get_current_user
from ..core.storage import get_presigned_url
from ..database import get_db
from ..models.plan import Plan
from ..models.project import Project
from ..models.schedule import Schedule, ScheduleStatus
from ..models.subscription import Subscription
from ..models.user import User, UserRole
from ..models.video import Video, VideoStatus
from ..models.video_job import JobStatus, VideoJob
from ..schemas.schedule import ScheduleCreate, ScheduleResponse
from ..schemas.video import (
    VideoGenerateRequest,
    VideoJobResponse,
    VideoListResponse,
    VideoResponse,
)

router = APIRouter(prefix="/videos", tags=["videos"])


def get_user_plan_limit(plan_name: str, db: Session) -> int:
    """Resolve a user's monthly video limit from the Plan table.

    Seeded plan names: starter / creator / pro / agency. Falls back to
    the starter limit if the plan row (or a legacy name) can't be resolved.
    """
    plan = db.query(Plan).filter(Plan.name == plan_name).first()
    if plan:
        return plan.video_limit_monthly
    legacy = {
        "scheduler": "creator",
        "committed": "pro",
        "intense": "agency",
    }
    plan = db.query(Plan).filter(Plan.name == legacy.get(plan_name, plan_name)).first()
    if plan:
        return plan.video_limit_monthly
    return settings.free_videos_per_month


def get_videos_this_month(user_id, db: Session) -> int:
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Video)
        .filter(
            Video.user_id == user_id,
            Video.created_at >= start_of_month,
        )
        .count()
    )


def enrich_video(video: Video, db: Session) -> VideoResponse:
    latest_job = db.query(VideoJob).filter(VideoJob.video_id == video.id).order_by(VideoJob.created_at.desc()).first()
    download_url = None
    if video.storage_key:
        with contextlib.suppress(Exception):
            download_url = get_presigned_url(video.storage_key)

    resp = VideoResponse.model_validate(video)
    resp.download_url = download_url
    resp.stream_url = download_url
    if latest_job:
        resp.latest_job = VideoJobResponse.model_validate(latest_job)

    project = db.query(Project).filter(Project.id == video.project_id).first()
    if project:
        resp.title = project.topic
        settings_json = project.settings_json or {}
        resp.platform = settings_json.get("platform", "youtube")
        resp.format = settings_json.get("format", "short-form")
        duration = settings_json.get("duration_seconds", 60)
        resp.duration = f"{int(duration)}s"

    schedule = db.query(Schedule).filter(Schedule.video_id == video.id).order_by(Schedule.created_at.desc()).first()
    if schedule:
        resp.schedule = {
            "id": str(schedule.id),
            "scheduled_at": schedule.scheduled_at.isoformat() if schedule.scheduled_at else None,
            "platform": schedule.platform.value if hasattr(schedule.platform, "value") else schedule.platform,
            "status": schedule.status.value if hasattr(schedule.status, "value") else schedule.status,
        }
    return resp


@router.post("/generate", response_model=VideoResponse, status_code=201)
async def generate_video(
    data: VideoGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check project ownership
    project = (
        db.query(Project)
        .filter(
            Project.id == data.project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check plan limits (admins are exempt from the paywall)
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan = sub.plan_name if sub else "starter"
    if current_user.role != UserRole.admin:
        limit = get_user_plan_limit(plan, db)
        count = get_videos_this_month(current_user.id, db)
        if count >= limit:
            raise HTTPException(
                status_code=402,
                detail=f"Monthly video limit reached ({limit}). Please upgrade your plan.",
            )

    # Create video record
    video = Video(
        project_id=data.project_id,
        user_id=current_user.id,
        status=VideoStatus.pending,
    )
    db.add(video)
    db.flush()

    # Create job record
    job = VideoJob(video_id=video.id, status=JobStatus.pending)
    db.add(job)
    db.commit()
    db.refresh(video)
    db.refresh(job)

    # Dispatch Celery task
    try:
        from app.celery_app import celery_app

        task = celery_app.send_task(
            "tasks.video_generation.generate_video",
            args=[
                str(video.id),
                str(job.id),
                data.topic,
                {
                    "tone": data.tone,
                    "style": data.style,
                    "duration_seconds": data.duration_seconds,
                    "plan": plan,
                    **(data.settings or {}),
                },
            ],
            queue="priority" if plan in ("pro", "agency") else "default",
        )
        job.celery_task_id = task.id
        db.commit()
    except Exception:
        # Celery may not be available in dev — job stays pending
        pass

    return enrich_video(video, db)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return enrich_video(video, db)


@router.get("/{video_id}/status", response_model=VideoResponse)
async def get_video_status(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return enrich_video(video, db)


@router.get("/{video_id}/download")
async def download_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if not video.storage_key:
        raise HTTPException(status_code=404, detail="Video file not ready")

    url = get_presigned_url(video.storage_key, expires_hours=1)
    return {"download_url": url}


@router.post("/{video_id}/regenerate", response_model=VideoResponse)
async def regenerate_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    project = db.query(Project).filter(Project.id == video.project_id).first()
    job = VideoJob(video_id=video.id, status=JobStatus.pending)
    db.add(job)
    video.status = VideoStatus.pending
    video.error_message = None
    db.commit()
    db.refresh(job)

    try:
        from app.celery_app import celery_app

        task = celery_app.send_task(
            "tasks.video_generation.generate_video",
            args=[str(video.id), str(job.id), project.topic if project else "", {"plan": "starter"}],
        )
        job.celery_task_id = task.id
        db.commit()
    except Exception:
        pass

    return enrich_video(video, db)


@router.post("/{video_id}/schedule", response_model=ScheduleResponse, status_code=201)
async def schedule_video(
    video_id: uuid.UUID,
    data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != VideoStatus.completed:
        raise HTTPException(status_code=400, detail="Video must be completed before scheduling")

    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan = sub.plan_name if sub else "starter"
    if data.platform == "youtube" and plan == "starter":
        raise HTTPException(
            status_code=402,
            detail="YouTube auto-publish requires a paid plan",
        )

    schedule = Schedule(
        video_id=video.id,
        user_id=current_user.id,
        platform=data.platform,
        scheduled_at=data.scheduled_at,
        status=ScheduleStatus.pending,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


@router.delete("/{video_id}")
async def delete_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(video)
    db.commit()
    return {"message": "Video deleted"}


@router.get("", response_model=VideoListResponse)
async def list_videos(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Video).filter(Video.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Video.created_at.desc()).offset(skip).limit(limit).all()
    return VideoListResponse(
        items=[enrich_video(v, db) for v in items],
        total=total,
    )
