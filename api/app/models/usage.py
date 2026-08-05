from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    # users.id is a UUID — match the type so the FK actually validates.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # event_type: 'video_generation', 'motion_credit_usage', 'storage_usage'
    event_type = Column(String, nullable=False)
    quantity = Column(Integer, default=1)

    # Detailed context (e.g., {'project_id': 5, 'video_id': 12})
    metadata_json = Column(JSON, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="usage_events")
