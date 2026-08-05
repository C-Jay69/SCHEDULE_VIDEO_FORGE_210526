import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_current_user
from ..database import get_db
from ..models.published_post import PublishedPost
from ..models.user import User
from ..models.video import Video
from ..schemas.users import PublishedPostResponse

router = APIRouter(prefix="/published", tags=["published"])


def _user_video_ids(db: Session, user_id) -> list:
    return [row[0] for row in db.query(Video.id).filter(Video.user_id == user_id).all()]


@router.get("", response_model=list[PublishedPostResponse])
async def list_published(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video_ids = _user_video_ids(db, current_user.id)
    if not video_ids:
        return []
    posts = (
        db.query(PublishedPost)
        .filter(PublishedPost.video_id.in_(video_ids))
        .order_by(PublishedPost.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [PublishedPostResponse.model_validate(p) for p in posts]


@router.get("/{post_id}", response_model=PublishedPostResponse)
async def get_published(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(PublishedPost).filter(PublishedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    video = db.query(Video).filter(Video.id == post.video_id).first()
    if not video or video.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return PublishedPostResponse.model_validate(post)
