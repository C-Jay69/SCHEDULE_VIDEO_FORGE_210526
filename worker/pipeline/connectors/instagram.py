import logging

from .base import BaseConnector, PlatformResult

logger = logging.getLogger(__name__)


class InstagramConnector(BaseConnector):
    platform_name = "instagram"

    def validate_token(self) -> bool:
        return False

    def refresh_access_token(self) -> str | None:
        return None

    def publish(self, video_path: str, title: str, description: str, tags: list) -> PlatformResult:
        """Instagram Reels requires highly approved Content Publishing API access."""
        logger.info("Instagram autopublish not available. Generating fallback package.")

        package_path = self.create_fallback_package(video_path, title, description, tags)

        return {
            "status": "fallback_needed",
            "platform_id": None,
            "url": None,
            "fallback_package_path": package_path,
            "error_message": "Official Instagram API for Reels requires elevated approval.",
        }
