import logging
from abc import ABC, abstractmethod
from typing import TypedDict

logger = logging.getLogger(__name__)


class PlatformResult(TypedDict):
    """Standardized result for all platform publishing attempts."""

    status: str  # 'published', 'fallback_needed', 'failed'
    platform_id: str | None
    url: str | None
    fallback_package_path: str | None  # Path to the zip/folder for manual upload
    error_message: str | None


class BaseConnector(ABC):
    """
    Base class for all social media platform connectors.
    Enforces a strict interface for publishing and token management.
    """

    platform_name: str = "base"

    def __init__(self, access_token: str, refresh_token: str | None = None):
        self.access_token = access_token
        self.refresh_token = refresh_token

    @abstractmethod
    def publish(self, video_path: str, title: str, description: str, tags: list) -> PlatformResult:
        """
        Attempt to publish a video to the platform.
        Must return a PlatformResult.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_token(self) -> bool:
        """Check if the current access token is still valid."""
        raise NotImplementedError

    @abstractmethod
    def refresh_access_token(self) -> str | None:
        """Refresh the access token. Returns the new token or None if refresh failed."""
        raise NotImplementedError

    def create_fallback_package(self, video_path: str, title: str, description: str, tags: list) -> str:
        """
        Generates a local package (video + text file) for manual upload.
        This is the 'compliant fallback' for platforms with restrictive APIs.
        """
        import shutil
        import uuid
        from pathlib import Path

        package_id = f"fallback_{self.platform_name}_{uuid.uuid4().hex[:8]}"
        package_dir = Path(f"/tmp/{package_id}")
        package_dir.mkdir(parents=True, exist_ok=True)

        # 1. Copy the video
        video_filename = f"video_{self.platform_name}.mp4"
        shutil.copy(video_path, package_dir / video_filename)

        # 2. Create metadata text file
        metadata_content = (
            f"Platform: {self.platform_name}\nTitle: {title}\n\nDescription:\n{description}\n\nTags: {', '.join(tags)}"
        )
        with open(package_dir / "metadata.txt", "w", encoding="utf-8") as f:
            f.write(metadata_content)

        # 3. Zip the package
        zip_path = shutil.make_archive(str(package_dir), "zip", package_dir)

        logger.info(f"Created fallback package for {self.platform_name} at {zip_path}")
        return zip_path
