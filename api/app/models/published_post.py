from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from ..database import Base


class PostStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    failed = "failed"


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    platform_url = Column(String(512), nullable=True)
    status = Column(Enum(PostStatus), default=PostStatus.pending, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    video = relationship("Video", back_populates="published_posts")
