import os

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery_app = Celery("videoforge", broker=broker_url, backend=result_backend)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tasks.video_generation.generate_video": {"queue": "default"},
        "tasks.publishing.publish_video": {"queue": "default"},
    },
)
