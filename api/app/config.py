from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    # App
    secret_key: str = secrets.token_urlsafe(32)
    app_url: str = "http://localhost:8000"
    next_public_app_url: str = "http://localhost:3000"
    # Comma-separated extra origins for CORS in addition to app_url + localhost:3000
    cors_allowed_origins: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Database
    database_url: str = "postgresql://videoforge:videoforge_secret@postgres:5432/videoforge"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "videoforge"
    minio_secure: bool = False

    # Admin
    admin_email: str = "admin@videoforge.io"
    admin_password: str = "adminpassword123"

    # Stripe
    stripe_publishable_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_creator_price_id: str = ""
    stripe_pro_price_id: str = ""

    # YouTube
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_redirect_uri: str = "http://localhost:8000/api/oauth/youtube/callback"

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    # Piper
    piper_model_path: str = "/app/models/en_US-lessac-medium.onnx"

    # Whisper
    whisper_model_size: str = "base"

    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Plan limits
    free_videos_per_month: int = 3
    creator_videos_per_month: int = 25
    pro_videos_per_month: int = 999999

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
