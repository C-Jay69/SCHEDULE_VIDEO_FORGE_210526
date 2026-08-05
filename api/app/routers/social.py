from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..core.security import get_current_user
from ..database import get_db
from ..models.social_account import SocialAccount
from ..models.user import User
from ..routers.oauth import get_flow

router = APIRouter(prefix="/social", tags=["social"])

PLATFORMS = ["youtube", "instagram", "tiktok", "x"]


@router.get("/connections")
async def get_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == current_user.id).all()
    connected = {a.platform: True for a in accounts}
    return {p: connected.get(p, False) for p in PLATFORMS}


@router.get("/youtube/auth")
async def youtube_auth_url(current_user: User = Depends(get_current_user)):
    if not settings.youtube_client_id:
        raise HTTPException(status_code=400, detail="YouTube OAuth not configured")

    flow = get_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(current_user.id),
        prompt="consent",
    )
    return {"auth_url": auth_url}


@router.delete("/{platform}")
async def disconnect_platform(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    account = (
        db.query(SocialAccount)
        .filter(SocialAccount.user_id == current_user.id, SocialAccount.platform == platform)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not connected")
    db.delete(account)
    db.commit()
    return {"message": f"{platform} disconnected"}
