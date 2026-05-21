import logging
from typing import Dict, Any, Optional
from .connectors.base import BaseConnector
from .connectors.youtube import YouTubeConnector
from .connectors.instagram import InstagramConnector
from .connectors.tiktok import TikTokConnector
from .connectors.x import XConnector

logger = logging.getLogger(__name__)

class PublishingOrchestrator:
    """
    Coordinates the publishing process across different social platforms.
    Decides whether to attempt direct API publishing or use the fallback method.
    """
    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}

    def register_connector(self, platform: str, connector: BaseConnector):
        self._connectors[platform] = connector
        logger.info(f"Registered connector: {platform}")

    async def publish_video(self, platform: str, video_path: str, title: str, description: str, tags: list) -> Dict[str, Any]:
        """
        Main entry point to publish a video.
        """
        connector = self._connectors.get(platform.lower())

        if not connector:
            error_msg = f"No connector registered for platform: {platform}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "platform_id": None,
                "url": None,
                "fallback_package_path": None,
                "error_message": error_msg
            }

        try:
            # 1. Check if token is valid
            if not connector.validate_token():
                logger.warning(f"Token invalid for {platform}. Attempting refresh...")
                new_token = connector.refresh_access_token()
                if not new_token:
                    return {
                        "status": "failed",
                        "platform_id": None,
                        "url": None,
                        "fallback_package_path": None,
                        "error_message": "Authentication failed. Please reconnect your account."
                    }
                # In a real app, we would update the DB with the new token here

            # 2. Attempt to publish
            logger.info(f"Starting publishing flow for {platform}...")
            result = connector.publish(video_path, title, description, tags)
            
            # 3. Log results
            if result["status"] == "published":
                logger.info(f"Successfully published to {platform}: {result['url']}")
            elif result["status"] == "fallback_needed":
                logger.info(f"Fallback required for {platform}. Package created at: {result['fallback_package_path']}")
            else:
                logger.error(f"Publishing failed for {platform}: {result['error_message']}")

            return result

        except Exception as e:
            logger.exception(f"Unexpected error in publishing flow for {platform}: {e}")
            return {
                "status": "failed",
                "platform_id": None,
                "url": None,
                "fallback_package_path": None,
                "error_message": str(e)
            }

# Global orchestrator instance
orchestrator = PublishingOrchestrator()
