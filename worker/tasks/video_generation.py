import os
import sys
import logging
import tempfile
import shutil
import json
from datetime import datetime, timezone

# Add api to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))

from celery_app import celery_app
from db import get_db_session

# Models
from app.models.video import Video, VideoStatus
from app.models.video_job import VideoJob, JobStatus
from app.models.user import User
from app.models.usage import UsageEvent
from app.models.schedule import Schedule
from app.models.project import Project

# Pipeline Components
from pipeline.text_generation import orchestrator as text_orchestrator
from pipeline.tts import generate_voiceover
from pipeline.stt import generate_subtitles
from pipeline.video_render import render_video
from pipeline.orchestrator import orchestrator as publish_orchestrator

logger = logging.getLogger(__name__)

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "videoforge")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


def update_job_progress(db, job, status: str, progress: int, error: str = None):
    """Update job status and progress. Idempotent."""
    job.status = JobStatus(status)
    job.progress_pct = progress
    if error:
        job.error = error
    db.commit()


def update_video_status(db, video, status: str, error: str = None, script: str = None, storage_key: str = None):
    """Update video record."""
    video.status = VideoStatus(status)
    if error:
        video.error_message = error
    if script:
        video.script_text = script
    if storage_key:
        video.storage_key = storage_key
    db.commit()


def upload_to_minio(file_path: str, object_name: str) -> str:
    """Upload file to MinIO storage."""
    from minio import Minio
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
    client.fput_object(MINIO_BUCKET, object_name, file_path, content_type="video/mp4")
    return object_name


@celery_app.task(
    name="tasks.video_generation.generate_video",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def generate_video(self, video_id: str, job_id: str, topic: str, settings: dict):
    """
    Full production-grade video generation pipeline:
    1. The Brain: Generate script & metadata (Ollama/OpenRouter)
    2. Creative: Generate voiceover (Piper) & subtitles (Whisper)
    3. Assembly: Render final video (FFmpeg)
    4. Storage: Upload to MinIO
    5. Social: Auto-publish or generate fallback package
    6. Accounting: Update user usage/credits
    """
    db = get_db_session()
    tmpdir = tempfile.mkdtemp(prefix="videoforge_")

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        user = db.query(User).filter(User.id == video.user_id).first()

        if not video or not job or not user:
            logger.error(f"Missing context: video={video_id}, job={job_id}, user={user.id if user else 'N/A'}")
            return

        plan = settings.get("plan", "free")
        tone = settings.get("tone", "engaging")
        style = settings.get("style", "informational")
        duration_seconds = settings.get("duration_seconds", 60)
        add_watermark = (plan == "free")

        # ── STEP 1: THE BRAIN (Text Generation) ──────────────────────────
        logger.info(f"[{video_id}] Phase 1: Generating script and metadata...")
        update_job_progress(db, job, "running", 5)
        update_video_status(db, video, "generating_script")

        # Get script
        script = await text_orchestrator.generate_script(topic, tone, style, duration_seconds)
        # Get metadata (Title, Tags, etc)
        metadata = await text_orchestrator.generate_metadata(topic)

        update_video_status(db, video, "generating_script", script=script)
        update_job_progress(db, job, "running", 20)
        logger.info(f"[{video_id}] Script/Metadata ready: {metadata.get('title')}")

        # ── STEP 2: CREATIVE (Audio & Subtitles) ─────────────────────────
        logger.info(f"[{video_id}] Phase 2: Generating audio and subtitles...")
        update_video_status(db, video, "generating_voiceover")
        update_job_progress(db, job, "running", 30)

        audio_path = os.path.join(tmpdir, "voiceover.wav")
        from pipeline.tts import generate_voiceover
        generate_voiceover(script, audio_path)
        
        logger.info(f"[{video_id}] Generating subtitles...")
        srt_path = os.path.join(tmpdir, "subtitles.srt")
        from pipeline.stt import generate_subtitles
        generate_subtitles(audio_path, srt_path)
        
        update_job_progress(db, job, "running", 50)
        logger.info(f"[{video_id}] Audio and subtitles ready.")

        # ── STEP 3: ASSEMBLY (Video Rendering) ──────────────────────────
        logger.info(f"[{video_id}] Phase 3: Rendering video...")
        update_video_status(db, video, "assembling")
        update_job_progress(db, job, "running", 65)

        output_path = os.path.join(tmpdir, f"{video_id}.mp4")
        from pipeline.video_render import render_video
        render_video(
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=output_path,
            topic=topic,
            add_watermark=add_watermark,
        )
        update_job_progress(db, job, "running", 85)
        logger.info(f"[{video_id}] Video assembly complete.")

        # ── STEP 4: STORAGE (MinIO) ─────────────────────────────────────
        logger.info(f"[{video_id}] Phase 4: Uploading to storage...")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        storage_key = f"videos/{video_id}/{timestamp}.mp4"
        upload_to_minio(output_path, storage_key)
        update_job_progress(db, job, "running", 90)
        logger.info(f"[{video_id}] Storage upload complete: {storage_key}")

        # ── STEP 5: SOCIAL (Publishing/Fallback) ─────────────────────────
        logger.info(f"[{video_id}] Phase 5: Handling social publishing...")
        
        # Check if there is a scheduled post for this video
        schedule = db.query(Schedule).filter(Schedule.video_id == video_id).first()
        
        if schedule:
            logger.info(f"[{video_id}] Found schedule for platform: {schedule.platform}")
            # In a real production app, we would use the user's OAuth tokens stored in the DB
            # For this implementation, we'll assume the connector is initialized with user tokens
            # (Mocking token retrieval for now)
            platform = schedule.platform
            token = "mock_token" 
            
            # Get the platform connector (this would usually be via a factory)
            from pipeline.connectors.youtube import YouTubeConnector
            from pipeline.connectors.instagram import InstagramConnector
            from pipeline.connectors.tiktok import TikTokConnector
            from pipeline.connectors.x import XConnector

            connector = None
            if platform == "youtube": connector = YouTubeConnector(token)
            elif platform == "instagram": connector = InstagramConnector(token)
            elif platform == "tiktok": connector = TikTokConnector(token)
            elif platform == "x": connector = XConnector(token)

            if connector:
                publish_result = await publish_orchestrator.publish_video(
                    platform=platform,
                    video_path=output_path,
                    title=metadata.get('title', topic),
                    description=metadata.get('description', ""),
                    tags=metadata.get('tags', [])
                )

                if publish_result["status"] == "published":
                    logger.info(f"[{video_id}] 🎉 SUCCESS: Published to {platform}")
                    # Link the schedule to the actual post
                    schedule.status = "published"
                    # (In a real app, we'd save the platform_id and URL to published_posts table)
                elif publish_result["status"] == "fallback_needed":
                    logger.info(f"[{video_id}] 📦 FALLBACK: Package created at {publish_result['fallback_package_path']}")
                    # Handle the fallback logic (e.g., notify user)
                else:
                    logger.error(f"[{video_id}] ❌ FAILED: {publish_result['error_message']}")
            else:
                logger.error(f"[{video_id}] No connector found for {platform}")

        # ── STEP 6: ACCOUNTING (Usage & Credits) ─────────────────────────
        logger.info(f"[{video_id}] Phase 6: Updating usage and credits...")
        
        # 1. Log the usage event
        usage_event = UsageEvent(
            user_id=user.id,
            event_type="video_generation",
            quantity=1,
            metadata_json={"video_id": str(video_id), "topic": topic}
        )
        db.add(usage_event)
        
        # 2. Subtract credits (Logic would depend on plan)
        # Note: In a real system, this would be a complex calculation based on plan limits
        # For now, we just record that the event happened.
        
        update_job_progress(db, job, "running", 98)

        # ── FINALIZATION ────────────────────────────────────────────────
        update_video_status(db, video, "completed", storage_key=storage_key, script=script)
        update_job_progress(db, job, "completed", 100)
        logger.info(f"[{video_id}] ✅ FULL PIPELINE COMPLETE.")

    except Exception as exc:
        logger.exception(f"[{video_id}] 💥 PIPELINE CRASHED: {exc}")
        try:
            from app.models.video import Video
            from app.models.video_job import VideoJob
            video = db.query(Video).filter(Video.id == video_id).first()
            job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
            if video:
                update_video_status(db, video, "failed", error=str(exc))
            if job:
                update_job_progress(db, job, "failed", job.progress_pct, error=str(exc))
        except Exception as db_err:
            logger.error(f"Failed to update failure status: {db_err}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        raise

    finally:
        db.close()
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
