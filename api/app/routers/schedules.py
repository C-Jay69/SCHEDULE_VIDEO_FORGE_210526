import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_current_user
from ..database import get_db
from ..models.schedule import Schedule, ScheduleStatus
from ..models.subscription import Subscription
from ..models.user import User, UserRole
from ..models.video import Video, VideoStatus
from ..schemas.schedule import (
    ScheduleCreate,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check video ownership and completion
    video = (
        db.query(Video)
        .filter(
            Video.id == data.video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != VideoStatus.completed:
        raise HTTPException(status_code=400, detail="Video must be completed before scheduling")

    # Check plan — only creator+ can auto-publish to YouTube (admins exempt)
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan = sub.plan_name if sub else "free"
    if data.platform == "youtube" and plan == "free" and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=402,
            detail="YouTube auto-publish requires Creator or Pro plan",
        )

    schedule = Schedule(
        video_id=data.video_id,
        user_id=current_user.id,
        platform=data.platform,
        scheduled_at=data.scheduled_at,
        status=ScheduleStatus.pending,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Schedule).filter(Schedule.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Schedule.scheduled_at.asc()).offset(skip).limit(limit).all()
    return ScheduleListResponse(items=[ScheduleResponse.model_validate(s) for s in items], total=total)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.id == schedule_id,
            Schedule.user_id == current_user.id,
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.status != ScheduleStatus.pending:
        raise HTTPException(status_code=400, detail="Only pending schedules can be edited")

    if data.scheduled_at is not None:
        schedule.scheduled_at = data.scheduled_at
    if data.platform is not None:
        schedule.platform = data.platform
    db.commit()
    db.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.id == schedule_id,
            Schedule.user_id == current_user.id,
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.status = ScheduleStatus.cancelled
    db.commit()
    return {"message": "Schedule cancelled"}


@router.post("/{schedule_id}/publish-now", response_model=ScheduleResponse)
async def publish_now(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = (
        db.query(Schedule)
        .filter(
            Schedule.id == schedule_id,
            Schedule.user_id == current_user.id,
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.status != ScheduleStatus.pending:
        raise HTTPException(status_code=400, detail="Schedule already processed")

    # Dispatch publishing task
    try:
        from worker.celery_app import celery_app

        celery_app.send_task(
            "tasks.publishing.publish_video",
            args=[str(schedule.id)],
        )
    except Exception:
        pass

    return ScheduleResponse.model_validate(schedule)
