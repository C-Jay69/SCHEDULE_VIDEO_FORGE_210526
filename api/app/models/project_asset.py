from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class ProjectAsset(Base):
    __tablename__ = "project_assets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # asset_type: 'script', 'audio', 'subtitle', 'thumbnail', 'final_video'
    asset_type = Column(String, nullable=False)
    storage_key = Column(String, nullable=False) # The S3 key
    original_filename = Column(String, nullable=True)
    
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="assets")
