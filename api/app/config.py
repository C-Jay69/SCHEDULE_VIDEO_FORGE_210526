import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    secret_key: str = secrets.token_urlsafe(32)
    app_url: str = "http://localhost:8011"
    next_public_app_url: str = "http://localhost:3000"
    # Comma-separated extra origins for CORS in addition to app_url + localhost:3000
    cors_allowed_origins: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Set the auth cookie Secure flag. Production is always served over HTTPS
    # (Caddy terminates TLS) so this defaults to True. Local dev over plain
    # HTTP/LAN should set COOKIE_SECURE=false.
    cookie_secure: bool = True

    # Database
    database_url: str = "postgresql://videoforge:videoforge_secret@postgres:5432/videoforge"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO (local dev) — production should set the AWS S3 aliases below,
    # which take precedence and let the same MinIO client talk to S3.
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "videoforge"
    minio_secure: bool = False

    # AWS S3 aliases (production). When AWS_ACCESS_KEY_ID or S3_BUCKET_NAME
    # are set, storage resolves to S3 instead of the MinIO dev defaults.
    s3_bucket_name: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_endpoint_url: str = ""

    # Admin
    admin_email: str = "admin@videoforge.io"
    admin_password: str = "adminpassword123"

    # Stripe
    stripe_publishable_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_starter_price_id: str = ""
    stripe_creator_price_id: str = ""
    stripe_pro_price_id: str = ""
    stripe_agency_price_id: str = ""
    # Add-on one-time payment price IDs (used by /billing/checkout/addon)
    stripe_addon_motion_price_id: str = ""
    stripe_addon_voice_cloning_price_id: str = ""
    stripe_addon_brand_kit_price_id: str = ""

    # YouTube
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_redirect_uri: str = "http://localhost:8011/api/oauth/youtube/callback"

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    # Magic Hour (AI video generation). Optional — when set, the worker renders
    # AI visuals for videos via the audio-to-video API instead of a static
    # gradient background.
    magic_hour_api_key: str = ""

    # Piper
    piper_model_path: str = "/app/models/en_US-lessac-medium.onnx"

    # Whisper
    whisper_model_size: str = "base"

    # SMTP (email) — optional. Leave empty to skip sending emails.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True

    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Plan limits
    free_videos_per_month: int = 3
    creator_videos_per_month: int = 25
    pro_videos_per_month: int = 999999

    # ── Storage resolution ─────────────────────────────────────────────
    # The API + worker use the MinIO client everywhere. When AWS S3 env vars
    # are present (production), resolve to S3; otherwise fall back to the
    # MinIO dev defaults. This keeps a single code path for both.
    @property
    def storage_endpoint(self) -> str:
        if self.aws_endpoint_url:
            return self.aws_endpoint_url
        if self.aws_access_key_id or self.s3_bucket_name:
            return f"s3.{self.aws_region}.amazonaws.com"
        return self.minio_endpoint

    @property
    def storage_access_key(self) -> str:
        return self.aws_access_key_id or self.minio_access_key

    @property
    def storage_secret_key(self) -> str:
        return self.aws_secret_access_key or self.minio_secret_key

    @property
    def storage_bucket(self) -> str:
        return self.s3_bucket_name or self.minio_bucket

    @property
    def storage_secure(self) -> bool:
        if self.aws_access_key_id or self.s3_bucket_name:
            return True
        return self.minio_secure

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
