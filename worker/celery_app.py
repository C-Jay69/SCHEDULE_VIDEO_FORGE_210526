import os
import sys

from celery import Celery
from celery.schedules import crontab

# Worker runs with api/app copied into the image (or available on PYTHONPATH
# in dev). Populate secrets from the configured backend (AWS Secrets Manager,
# file mounts) BEFORE reading broker/backend URLs — same as the API does.
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
try:
    from app.core.secrets import populate_environ

    populate_environ()
except Exception:  # app package not importable yet (CI/test) — env mode is fine
    pass

broker_url = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery_app = Celery(
    "videoforge",
    broker=broker_url,
    backend=result_backend,
    include=[
        "tasks.video_generation",
        "tasks.publishing",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.video_generation.generate_video": {"queue": "default"},
        "tasks.publishing.publish_video": {"queue": "default"},
    },
    beat_schedule={
        "process-scheduled-publishes": {
            "task": "tasks.publishing.process_scheduled",
            "schedule": crontab(minute="*/5"),  # every 5 minutes
        },
    },
)
