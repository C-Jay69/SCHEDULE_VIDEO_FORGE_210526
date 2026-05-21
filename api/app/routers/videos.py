from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
import uuid
from ..database import get_db
from ..models.user import User
from ..models.video import Video, VideoStatus
from ..models.video_job import VideoJob, JobStatus
from ..models.project import Project
from ..models.subscription import Subscription, PlanType
from ..schemas.video import VideoResponse, VideoListResponse, VideoGenerateRequest, VideoJobResponse
from ..core.security import get_current_user
from ..core.storage import get_presigned_url
from ..config import settings

router = APIRouter(prefix="/videos", tags=["videos"])


def get_user_plan_limit(plan: str) -> int:
    limits = {
        "free": settings.free_videos_per_month,
        "creator": settings.creator_videos_per_month,
        "pro": settings.pro_videos_per_month,
    }
    return limits.get(plan, settings.free_videos_per_month)


def get_videos_this_month(user_id, db: Session) -> int:
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return db.query(Video).filter(
        Video.user_id == user_id,
        Video.created_at >= start_of_month,
    ).count()


def enrich_video(video: Video, db: Session) -> VideoResponse:
    latest_job = (
        db.query(VideoJob)
        .filter(VideoJob.video_id == video.id)
        .order_by(VideoJob.created_at.desc())
        .first()
    )
    download_url = None
    if video.storage_key:
        try:
            download_url = get_presigned_url(video.storage_key)
        except Exception:
            pass

    resp = VideoResponse.model_validate(video)
    resp.download_url = download_url
    if latest_job:
        resp.latest_job = VideoJobResponse.model_validate(latest_job)
    return resp


@router.post("/generate", response_model=VideoResponse, status_code=201)
async def generate_video(
    data: VideoGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check project ownership
    project = db.query(Project).filter(
        Project.id == data.project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check plan limits
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan = sub.plan.value if sub else "free"
    limit = get_user_plan_limit(plan)
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
        from worker.celery_app import celery_app
        task = celery_app.send_task(
            "tasks.video_generation.generate_video",
            args=[str(video.id), str(job.id), data.topic, {
                "tone": data.tone,
                "style": data.style,
                "duration_seconds": data.duration_seconds,
                "plan": plan,
                **(data.settings or {}),
            }],
            queue="priority" if plan == "pro" else "default",
        )
        job.celery_task_id = task.id
        db.commit()
    except Exception as e:
        # Celery may not be available in dev — job stays pending
        pass

    return enrich_video(video, db)


@router.get("/{video_id}/status", response_model=VideoResponse)
async def get_video_status(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id,
    ).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return enrich_video(video, db)


@router.get("/{video_id}/download")
async def download_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id,
    ).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if not video.storage_key:
        raise HTTPException(status_code=404, detail="Video file not ready")

    url = get_presigned_url(video.storage_key, expires_hours=1)
    return {"download_url": url}


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
