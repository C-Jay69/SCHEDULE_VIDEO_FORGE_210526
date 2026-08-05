import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ScheduleStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    failed = "failed"
    cancelled = "cancelled"


class PlatformType(str, enum.Enum):
    youtube = "youtube"
    instagram = "instagram"
    tiktok = "tiktok"
    x = "x"


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="schedules")
    user = relationship("User", back_populates="schedules")
