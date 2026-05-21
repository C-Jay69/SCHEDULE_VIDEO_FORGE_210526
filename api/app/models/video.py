from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from ..database import Base


class VideoStatus(str, enum.Enum):
    pending = "pending"
    generating_script = "generating_script"
    generating_voiceover = "generating_voiceover"
    generating_subtitles = "generating_subtitles"
    assembling = "assembling"
    completed = "completed"
    failed = "failed"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(VideoStatus), default=VideoStatus.pending, nullable=False)
    storage_key = Column(String(512), nullable=True)
    script_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="videos")
    user = relationship("User", back_populates="videos")
    jobs = relationship("VideoJob", back_populates="video", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="video", cascade="all, delete-orphan")
    published_posts = relationship("PublishedPost", back_populates="video", cascade="all, delete-orphan")
