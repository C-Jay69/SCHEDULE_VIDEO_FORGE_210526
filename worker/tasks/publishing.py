import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))

from app.config import settings

from celery_app import celery_app
from db import get_db_session

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")


def download_video_from_minio(storage_key: str, dest_path: str):
    from minio import Minio

    client = Minio(
        settings.storage_endpoint,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key,
        secure=settings.storage_secure,
        region=settings.aws_region if settings.aws_access_key_id or settings.s3_bucket_name else None,
    )
    client.fget_object(settings.storage_bucket, storage_key, dest_path)


def get_decrypted_token(encrypted: str) -> str:
    import base64
    import hashlib

    from cryptography.fernet import Fernet

    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)
    return f.decrypt(encrypted.encode()).decode()


@celery_app.task(
    name="tasks.publishing.publish_video",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
)
def publish_video(self, schedule_id: str):
    """Publish a scheduled video to its target platform."""
    db = get_db_session()

    try:
        from app.models.published_post import PostStatus, PublishedPost
        from app.models.schedule import Schedule, ScheduleStatus
        from app.models.social_account import SocialAccount

        from pipeline.text_generation import generate_title_and_tags

        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            logger.error(f"Schedule not found: {schedule_id}")
            return

        if schedule.status != ScheduleStatus.pending:
            logger.warning(f"Schedule {schedule_id} already processed")
            return

        video = schedule.video
        if not video or not video.storage_key:
            raise RuntimeError("Video file not ready")

        platform = schedule.platform.value if hasattr(schedule.platform, "value") else schedule.platform
        logger.info(f"Publishing video {video.id} to {platform}")

        # Get metadata
        topic = video.project.topic if video.project else "video"
        import asyncio

        meta = asyncio.run(generate_title_and_tags(topic))

        # Handle non-YouTube platforms (manual export)
        if platform != "youtube":
            post = PublishedPost(
                video_id=video.id,
                platform=platform,
                platform_url=None,
                status=PostStatus.published,
                error_message=f"Manual upload required for {platform}. Download your video and upload manually.",
            )
            db.add(post)
            schedule.status = ScheduleStatus.published
            db.commit()
            logger.info(f"Non-YouTube platform {platform}: metadata export ready")
            return

        # YouTube: find connected account
        social_account = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.user_id == schedule.user_id,
                SocialAccount.platform == "youtube",
            )
            .first()
        )
        if not social_account:
            raise RuntimeError("YouTube account not connected")

        # Decrypt tokens
        access_token = get_decrypted_token(social_account.access_token_encrypted)
        refresh_token = (
            get_decrypted_token(social_account.refresh_token_encrypted)
            if social_account.refresh_token_encrypted
            else None
        )

        # Download video
        tmpdir = tempfile.mkdtemp()
        local_video_path = os.path.join(tmpdir, f"{video.id}.mp4")
        download_video_from_minio(video.storage_key, local_video_path)

        # Upload to YouTube
        from pipeline.connectors.youtube import YouTubeConnector

        connector = YouTubeConnector(access_token=access_token, refresh_token=refresh_token)
        from pipeline.orchestrator import orchestrator

        orchestrator.register_connector("youtube", connector)

        # Refresh token if needed
        if not connector.validate_token():
            new_token = connector.refresh_access_token()
            if not new_token:
                raise RuntimeError("YouTube token expired and refresh failed")
            # Save new token
            from app.core.encryption import encrypt_token

            social_account.access_token_encrypted = encrypt_token(new_token)
            db.commit()

        result = connector.publish(
            video_path=local_video_path,
            title=meta["title"],
            description=meta["description"],
            tags=meta["tags"],
        )

        # Record published post
        post = PublishedPost(
            video_id=video.id,
            platform="youtube",
            platform_url=result.get("url"),
            status=PostStatus.published,
        )
        db.add(post)
        schedule.status = ScheduleStatus.published
        db.commit()

        logger.info(f"✓ Published to YouTube: {result.get('url')}")

        # Cleanup
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as exc:
        logger.error(f"Publishing failed for schedule {schedule_id}: {exc}", exc_info=True)
        try:
            from app.models.published_post import PostStatus, PublishedPost
            from app.models.schedule import Schedule, ScheduleStatus

            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if schedule:
                schedule.status = ScheduleStatus.failed
                post = PublishedPost(
                    video_id=schedule.video_id,
                    platform=schedule.platform.value if hasattr(schedule.platform, "value") else schedule.platform,
                    status=PostStatus.failed,
                    error_message=str(exc),
                )
                db.add(post)
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to record publish failure: {db_err}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=120) from None
        raise

    finally:
        db.close()


@celery_app.task(name="tasks.publishing.process_scheduled")
def process_scheduled():
    """Beat task: check for due schedules and trigger publishing."""
    from datetime import datetime, timezone

    db = get_db_session()
    try:
        from app.models.schedule import Schedule, ScheduleStatus

        now = datetime.now(timezone.utc)
        due = (
            db.query(Schedule)
            .filter(
                Schedule.status == ScheduleStatus.pending,
                Schedule.scheduled_at <= now,
            )
            .all()
        )
        for schedule in due:
            logger.info(f"Triggering publish for schedule {schedule.id}")
            publish_video.delay(str(schedule.id))
    except Exception as e:
        logger.error(f"process_scheduled error: {e}")
    finally:
        db.close()
