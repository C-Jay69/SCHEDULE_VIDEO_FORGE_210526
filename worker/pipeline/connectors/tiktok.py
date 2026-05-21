import logging
from typing import Optional
from .base import BaseConnector, PlatformResult

logger = logging.getLogger(__name__)

class TikTokConnector(BaseConnector):
    platform_name = "tiktok"

    def validate_token(self) -> bool:
        # TikTok API access is highly restricted for autopublishing
        return False

    def refresh_access_token(self) -> Optional[str]:
        return None

    def publish(self, video_path: str, title: str, description: str, tags: list) -> PlatformResult:
        """TikTok requires manual upload or highly approved API access."""
        logger.info(f"TikTok autopublish not available. Generating fallback package.")
        
        package_path = self.create_fallback_package(video_path, title, description, tags)
        
        return {
            "status": "fallback_needed",
            "platform_id": None,
            "url": None,
            "fallback_package_path": package_path,
            "error_message": "Official TikTok API for autopublishing requires elevated approval."
        }
