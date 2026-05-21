from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from ..database import get_db
from ..models.user import User
from ..models.social_account import SocialAccount
from ..core.security import get_current_user, get_token_from_request, decode_token
from ..core.encryption import encrypt_token
from ..config import settings
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/oauth", tags=["oauth"])

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def get_flow():
    client_config = {
        "web": {
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.youtube_redirect_uri],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = settings.youtube_redirect_uri
    return flow


@router.get("/youtube/connect")
async def youtube_connect(request: Request, current_user: User = Depends(get_current_user)):
    if not settings.youtube_client_id:
        raise HTTPException(status_code=400, detail="YouTube OAuth not configured")
    
    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(current_user.id),
        prompt="consent",
    )
    return {"auth_url": auth_url}


@router.get("/youtube/callback")
async def youtube_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db),
):
    if error:
        return RedirectResponse(url=f"{settings.next_public_app_url}/connect?error={error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    user = db.query(User).filter(User.id == state).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid state")

    flow = get_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Get channel info
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", credentials=credentials)
        channel_resp = youtube.channels().list(part="snippet", mine=True).execute()
        channel_name = channel_resp["items"][0]["snippet"]["title"] if channel_resp.get("items") else "YouTube"
    except Exception:
        channel_name = "YouTube"

    # Save / update social account
    existing = db.query(SocialAccount).filter(
        SocialAccount.user_id == user.id,
        SocialAccount.platform == "youtube",
    ).first()

    if existing:
        existing.account_name = channel_name
        existing.access_token_encrypted = encrypt_token(credentials.token)
        existing.refresh_token_encrypted = encrypt_token(credentials.refresh_token or "")
        existing.expires_at = credentials.expiry
    else:
        account = SocialAccount(
            user_id=user.id,
            platform="youtube",
            account_name=channel_name,
            access_token_encrypted=encrypt_token(credentials.token),
            refresh_token_encrypted=encrypt_token(credentials.refresh_token or ""),
            expires_at=credentials.expiry,
        )
        db.add(account)

    db.commit()
    return RedirectResponse(url=f"{settings.next_public_app_url}/connect?success=youtube")
