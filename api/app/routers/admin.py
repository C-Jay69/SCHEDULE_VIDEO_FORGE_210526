from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
import uuid
from ..database import get_db
from ..models.user import User, UserRole
from ..models.subscription import Subscription
from ..models.video import Video
from ..models.video_job import VideoJob, JobStatus
from ..models.system_settings import SystemSettings
from ..models.admin_audit_log import AdminAuditLog
from ..schemas.admin import (
    AdminMetrics, AdminUserResponse, AdminJobResponse,
    SystemSettingResponse, SystemSettingUpdate, AdminUserUpdate, AuditLogResponse
)
from ..core.security import get_current_admin
from typing import List, Optional

router = APIRouter(prefix="/admin", tags=["admin"])


def log_action(db: Session, admin: User, action: str, target: str = None):
    log = AdminAuditLog(admin_id=admin.id, action=action, target=target)
    db.add(log)
    db.commit()


@router.get("/metrics", response_model=AdminMetrics)
async def get_metrics(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(User).count()
    new_users_7d = db.query(User).filter(User.created_at >= seven_days_ago).count()
    active_subs = db.query(Subscription).filter(Subscription.status == "active").count()
    videos_today = db.query(Video).filter(Video.created_at >= start_of_day).count()
    videos_month = db.query(Video).filter(Video.created_at >= start_of_month).count()
    queued = db.query(VideoJob).filter(VideoJob.status == JobStatus.pending).count()
    running = db.query(VideoJob).filter(VideoJob.status == JobStatus.running).count()
    failed = db.query(VideoJob).filter(VideoJob.status == JobStatus.failed).count()

    return AdminMetrics(
        total_users=total_users,
        new_users_7d=new_users_7d,
        active_subscriptions=active_subs,
        videos_today=videos_today,
        videos_this_month=videos_month,
        queued_jobs=queued,
        running_jobs=running,
        failed_jobs=failed,
    )


@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search:
        query = query.filter(User.email.ilike(f"%{search}%") | User.name.ilike(f"%{search}%"))
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for u in users:
        sub = (
            db.query(Subscription)
            .filter(Subscription.user_id == u.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )
        video_count = db.query(Video).filter(Video.user_id == u.id).count()
        resp = AdminUserResponse.model_validate(u)
        resp.subscription_plan = sub.plan.value if sub else "free"
        resp.video_count = video_count
        result.append(resp)
    return result


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: AdminUserUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = UserRole(data.role)
    if data.name is not None:
        user.name = data.name

    db.commit()
    db.refresh(user)
    log_action(db, admin, f"update_user:{data.model_dump(exclude_none=True)}", str(user_id))

    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    video_count = db.query(Video).filter(Video.user_id == user.id).count()
    resp = AdminUserResponse.model_validate(user)
    resp.subscription_plan = sub.plan.value if sub else "free"
    resp.video_count = video_count
    return resp


@router.get("/jobs", response_model=List[AdminJobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(VideoJob)
    if status:
        query = query.filter(VideoJob.status == status)
    jobs = query.order_by(VideoJob.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for job in jobs:
        resp = AdminJobResponse.model_validate(job)
        if job.video:
            if job.video.user:
                resp.user_email = job.video.user.email
            if job.video.project:
                resp.topic = job.video.project.topic
        result.append(resp)
    return result


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in (JobStatus.failed, JobStatus.pending):
        raise HTTPException(status_code=400, detail="Job is not in a retryable state")

    job.status = JobStatus.pending
    job.progress_pct = 0
    job.error = None
    db.commit()

    try:
        from worker.celery_app import celery_app
        video = job.video
        plan = "free"
        if video and video.user:
            sub = (
                db.query(Subscription)
                .filter(Subscription.user_id == video.user_id)
                .order_by(Subscription.created_at.desc())
                .first()
            )
            if sub:
                plan = sub.plan.value
        topic = video.project.topic if video and video.project else ""
        task = celery_app.send_task(
            "tasks.video_generation.generate_video",
            args=[str(job.video_id), str(job.id), topic, {"plan": plan}],
        )
        job.celery_task_id = task.id
        db.commit()
    except Exception:
        pass

    log_action(db, admin, "retry_job", str(job_id))
    return {"status": "queued", "job_id": str(job_id)}


@router.get("/settings", response_model=List[SystemSettingResponse])
async def get_settings(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    settings_list = db.query(SystemSettings).all()
    return [SystemSettingResponse.model_validate(s) for s in settings_list]


@router.put("/settings/{key}", response_model=SystemSettingResponse)
async def update_setting(
    key: str,
    data: SystemSettingUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if not setting:
        setting = SystemSettings(key=key, value=data.value)
        db.add(setting)
    else:
        setting.value = data.value
    db.commit()
    db.refresh(setting)
    log_action(db, admin, f"update_setting:{key}", data.value)
    return SystemSettingResponse.model_validate(setting)


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = []
    for log in logs:
        resp = AuditLogResponse.model_validate(log)
        if log.admin:
            resp.admin_email = log.admin.email
        result.append(resp)
    return result
