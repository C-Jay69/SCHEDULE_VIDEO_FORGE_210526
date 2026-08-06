import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.security import get_current_admin, get_password_hash
from ..database import get_db
from ..models.admin_audit_log import AdminAuditLog
from ..models.plan import Plan
from ..models.published_post import PublishedPost
from ..models.schedule import Schedule
from ..models.subscription import Subscription
from ..models.system_settings import SystemSettings
from ..models.user import User, UserRole
from ..models.video import Video
from ..models.video_job import JobStatus, VideoJob
from ..models.webhook_event import WebhookEvent
from ..schemas.admin import (
    AdminJobResponse,
    AdminMetrics,
    AdminUserResponse,
    AdminUserUpdate,
    AuditLogResponse,
    SystemSettingCreate,
    SystemSettingResponse,
    SystemSettingUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def log_action(db: Session, admin: User, action: str, target: str | None = None):
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
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    active_subs = db.query(Subscription).filter(Subscription.status == "active").count()
    videos_today = db.query(Video).filter(Video.created_at >= start_of_day).count()
    videos_month = db.query(Video).filter(Video.created_at >= start_of_month).count()
    total_videos = db.query(Video).count()
    total_schedules = db.query(Schedule).count()
    total_published = db.query(PublishedPost).count()
    queued = db.query(VideoJob).filter(VideoJob.status == JobStatus.pending).count()
    running = db.query(VideoJob).filter(VideoJob.status == JobStatus.running).count()
    failed = db.query(VideoJob).filter(VideoJob.status == JobStatus.failed).count()

    # MRR estimate: sum price_cents of active subscriptions by plan.
    mrr_cents = 0
    active_rows = (
        db.query(Plan.name, func.count(Subscription.id))
        .join(Subscription, Subscription.plan_id == Plan.id)
        .filter(Subscription.status == "active")
        .group_by(Plan.name)
        .all()
    )
    for plan_name, count in active_rows:
        plan_row = db.query(Plan).filter(Plan.name == plan_name).first()
        if plan_row:
            mrr_cents += plan_row.price_cents * count

    storage_used = db.query(Video).count() * 5  # ~5MB per video estimate
    published_by_platform = dict(
        db.query(PublishedPost.platform, func.count(PublishedPost.id)).group_by(PublishedPost.platform).all()
    )

    return AdminMetrics(
        total_users=total_users,
        new_users_7d=new_users_7d,
        active_subscriptions=active_subs,
        active_users=active_users,
        videos_today=videos_today,
        videos_this_month=videos_month,
        total_videos=total_videos,
        total_schedules=total_schedules,
        total_published=total_published,
        queued_jobs=queued,
        running_jobs=running,
        failed_jobs=failed,
        mrr_cents=mrr_cents,
        storage_used_mb=storage_used,
        published_by_platform=published_by_platform,
    )


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
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
            db.query(Subscription).filter(Subscription.user_id == u.id).order_by(Subscription.created_at.desc()).first()
        )
        video_count = db.query(Video).filter(Video.user_id == u.id).count()
        resp = AdminUserResponse.model_validate(u)
        resp.subscription_plan = sub.plan_name if sub else "starter"
        resp.video_count = video_count
        result.append(resp)
    return result


@router.put("/users/{user_id}", response_model=AdminUserResponse)
@router.patch("/users/{user_id}", response_model=AdminUserResponse)
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
        db.query(Subscription).filter(Subscription.user_id == user.id).order_by(Subscription.created_at.desc()).first()
    )
    video_count = db.query(Video).filter(Video.user_id == user.id).count()
    resp = AdminUserResponse.model_validate(user)
    resp.subscription_plan = sub.plan_name if sub else "starter"
    resp.video_count = video_count
    return resp


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user_detail(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sub = (
        db.query(Subscription).filter(Subscription.user_id == user.id).order_by(Subscription.created_at.desc()).first()
    )
    video_count = db.query(Video).filter(Video.user_id == user.id).count()
    resp = AdminUserResponse.model_validate(user)
    resp.subscription_plan = sub.plan_name if sub else "starter"
    resp.video_count = video_count
    return resp


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = False
    db.commit()
    log_action(db, admin, "deactivate_user", str(user_id))
    return {"message": "User deactivated"}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    temp_password = f"vf-{uuid.uuid4().hex[:12]}"
    user.password_hash = get_password_hash(temp_password)
    db.commit()
    log_action(db, admin, "reset_password", str(user_id))
    return {"message": "Password reset", "temporary_password": temp_password}


@router.get("/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    base_query = db.query(VideoJob)
    if status:
        base_query = base_query.filter(VideoJob.status == status)
    total = base_query.count()
    jobs = base_query.order_by(VideoJob.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for job in jobs:
        resp = AdminJobResponse.model_validate(job)
        if job.video:
            if job.video.user:
                resp.user_email = job.video.user.email
            if job.video.project:
                resp.topic = job.video.project.topic
        result.append(resp)
    return {"jobs": result, "total": total}


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
        from app.celery_app import celery_app

        video = job.video
        plan = "starter"
        if video and video.user:
            sub = (
                db.query(Subscription)
                .filter(Subscription.user_id == video.user_id)
                .order_by(Subscription.created_at.desc())
                .first()
            )
            if sub:
                plan = sub.plan_name
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


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    log_action(db, admin, "delete_job", str(job_id))
    return {"message": "Job deleted"}


@router.get("/settings", response_model=list[SystemSettingResponse])
async def get_settings(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    settings_list = db.query(SystemSettings).all()
    result = []
    for s in settings_list:
        resp = SystemSettingResponse.model_validate(s)
        resp.id = s.key
        result.append(resp)
    return result


@router.post("/settings", response_model=SystemSettingResponse, status_code=201)
async def add_setting(
    data: SystemSettingCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    setting = db.query(SystemSettings).filter(SystemSettings.key == data.key).first()
    if setting:
        raise HTTPException(status_code=400, detail="Setting already exists")
    setting = SystemSettings(key=data.key, value=data.value)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    log_action(db, admin, f"add_setting:{data.key}", data.value)
    resp = SystemSettingResponse.model_validate(setting)
    resp.id = setting.key
    resp.description = data.description
    return resp


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
        if data.value is not None:
            setting.value = data.value
    db.commit()
    db.refresh(setting)
    log_action(db, admin, f"update_setting:{key}", data.value)
    resp = SystemSettingResponse.model_validate(setting)
    resp.id = setting.key
    resp.description = data.description
    return resp


@router.delete("/settings/{key}")
async def delete_setting(
    key: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(setting)
    db.commit()
    log_action(db, admin, f"delete_setting:{key}", key)
    return {"message": "Setting deleted"}


@router.post("/maintenance/toggle")
async def toggle_maintenance(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    setting = db.query(SystemSettings).filter(SystemSettings.key == "maintenance_mode").first()
    currently_on = setting is not None and setting.value == "true"
    new_value = "false" if currently_on else "true"
    if setting:
        setting.value = new_value
    else:
        setting = SystemSettings(key="maintenance_mode", value=new_value)
        db.add(setting)
    db.commit()
    log_action(db, admin, f"maintenance_toggle:{new_value}", new_value)
    # Bust the middleware cache so the change applies immediately.
    from ..core.middleware import _maint_state

    _maint_state.update({"enabled": new_value == "true", "checked_at": 0.0})
    return {"maintenance_mode": new_value == "true"}


@router.get("/webhooks", response_model=list[dict])
async def get_webhooks(
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    events = db.query(WebhookEvent).order_by(WebhookEvent.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(e.id),
            "provider": e.provider,
            "event_type": e.event_type,
            "processed": e.processed,
            "error_message": e.error_message,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logs = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for log in logs:
        resp = AuditLogResponse.model_validate(log)
        if log.admin:
            resp.admin_email = log.admin.email
        result.append(resp)
    return result
