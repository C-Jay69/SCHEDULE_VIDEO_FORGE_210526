import io
import logging

from minio import Minio
from minio.error import S3Error

from ..config import settings

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    return Minio(
        settings.storage_endpoint,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key,
        secure=settings.storage_secure,
        region=settings.aws_region if settings.aws_access_key_id or settings.s3_bucket_name else None,
    )


def ensure_bucket_exists():
    client = get_minio_client()
    try:
        if not client.bucket_exists(settings.storage_bucket):
            client.make_bucket(settings.storage_bucket)
            logger.info(f"Created bucket: {settings.storage_bucket}")
    except S3Error as e:
        logger.error(f"MinIO bucket setup error: {e}")


def upload_file(file_path: str, object_name: str, content_type: str = "application/octet-stream") -> str:
    client = get_minio_client()
    client.fput_object(
        settings.storage_bucket,
        object_name,
        file_path,
        content_type=content_type,
    )
    return object_name


def upload_bytes(data: bytes, object_name: str, content_type: str = "application/octet-stream") -> str:
    client = get_minio_client()
    client.put_object(
        settings.storage_bucket,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_name


def get_presigned_url(object_name: str, expires_hours: int = 24) -> str:
    from datetime import timedelta

    client = get_minio_client()
    url = client.presigned_get_object(
        settings.storage_bucket,
        object_name,
        expires=timedelta(hours=expires_hours),
    )
    return url


def delete_file(object_name: str):
    client = get_minio_client()
    try:
        client.remove_object(settings.storage_bucket, object_name)
    except S3Error as e:
        logger.warning(f"Failed to delete {object_name}: {e}")


def download_file(object_name: str, dest_path: str):
    client = get_minio_client()
    client.fget_object(settings.storage_bucket, object_name, dest_path)
