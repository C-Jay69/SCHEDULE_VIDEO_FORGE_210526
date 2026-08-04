from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    stripe_price_id = Column(String, unique=True, nullable=True)
    
    # Limits
    video_limit_monthly = Column(Integer, default=3)
    storage_limit_gb = Column(Integer, default=1)
    motion_credits_monthly = Column(Integer, default=0)
    
    # Features (stored as JSON: ["no watermark", "auto-post", etc])
    features_json = Column(JSON, default=list)
    
    price_cents = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="plan_rel")
