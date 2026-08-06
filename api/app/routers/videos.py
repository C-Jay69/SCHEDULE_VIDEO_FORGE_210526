import contextlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..core.security import get_current_user
from ..core.storage import delete_file, get_object_reader, get_object_size
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

    resp = VideoResponse.model_validate(video)
    # Browser playback goes through the authenticated /stream endpoint
    # (same-origin, via the Next.js /api proxy) rather than a presigned URL,
    # which would point at the internal MinIO host unreachable from browsers.
    resp.stream_url = f"/api/videos/{video.id}/stream"
    resp.download_url = None
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
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _stream_video_file(video_id, request, current_user, db, as_attachment=True)


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _stream_video_file(video_id, request, current_user, db, as_attachment=False)


def _stream_video_file(
    video_id: uuid.UUID,
    request: Request,
    current_user: User,
    db: Session,
    as_attachment: bool,
):
    """Stream a video file from storage with HTTP Range support.

    Browsers can't reach the internal MinIO host, so playback/download is
    proxied through the authenticated API. Range requests get a 206 partial
    response, enabling seeking in the HTML5 player.
    """
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

    total = get_object_size(video.storage_key)
    media_type = "video/mp4"
    headers = {"Accept-Ranges": "bytes"}
    if as_attachment:
        filename = f"videoforge-{video_id}.mp4"
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    range_header = request.headers.get("range")
    parsed = _parse_range(range_header, total)
    if parsed:
        start, end, length = parsed
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
        headers["Content-Length"] = str(length)
        return StreamingResponse(
            get_object_reader(video.storage_key, offset=start, length=length),
            status_code=206,
            headers=headers,
            media_type=media_type,
        )

    headers["Content-Length"] = str(total)
    return StreamingResponse(
        get_object_reader(video.storage_key),
        status_code=200,
        headers=headers,
        media_type=media_type,
    )


def _parse_range(range_header: str | None, total: int) -> tuple[int, int, int] | None:
    """Parse a single `bytes=start-end` range into (start, end, length)."""
    if not range_header or not range_header.startswith("bytes="):
        return None
    try:
        start_str, end_str = range_header[len("bytes=") :].split("-", 1)
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else total - 1
    except ValueError:
        return None
    if start < 0 or start >= total:
        return None
    end = min(end, total - 1)
    return start, end, end - start + 1


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
    if video.storage_key:
        with contextlib.suppress(Exception):
            delete_file(video.storage_key)
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
