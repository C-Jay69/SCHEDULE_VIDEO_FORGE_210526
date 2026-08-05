import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .base import BaseConnector, PlatformResult

logger = logging.getLogger(__name__)

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")


class YouTubeConnector(BaseConnector):
    platform_name = "youtube"

    def __init__(self, access_token: str, refresh_token: str | None = None):
        super().__init__(access_token, refresh_token)
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service

        credentials = Credentials(
            token=self.access_token,
            refresh_token=self.refresh_token,
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token",
        )
        self._service = build("youtube", "v3", credentials=credentials)
        return self._service

    def validate_token(self) -> bool:
        try:
            service = self._get_service()
            service.channels().list(part="id", mine=True).execute()
            return True
        except Exception as e:
            logger.warning(f"YouTube token validation failed: {e}")
            return False

    def refresh_access_token(self) -> str | None:
        try:
            credentials = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                client_id=YOUTUBE_CLIENT_ID,
                client_secret=YOUTUBE_CLIENT_SECRET,
                token_uri="https://oauth2.googleapis.com/token",
            )
            credentials.refresh(Request())
            self.access_token = credentials.token
            return credentials.token
        except Exception as e:
            logger.error(f"YouTube token refresh failed: {e}")
            return None

    def publish(self, video_path: str, title: str, description: str, tags: list) -> PlatformResult:
        """Upload video to YouTube using Data API v3."""
        try:
            service = self._get_service()

            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": tags[:500],
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                },
            }

            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=1024 * 1024,  # 1MB chunks
            )

            request = service.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"YouTube upload progress: {progress}%")

            video_id = response.get("id")
            return {
                "status": "published",
                "platform_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "fallback_package_path": None,
                "error_message": None,
            }

        except Exception as e:
            logger.error(f"YouTube publish failed: {e}")
            return {
                "status": "failed",
                "platform_id": None,
                "url": None,
                "fallback_package_path": None,
                "error_message": str(e),
            }
