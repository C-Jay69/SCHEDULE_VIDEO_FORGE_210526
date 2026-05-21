from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False) # e.g., 'DEACTIVATE_USER', 'CHANGE_PLAN'
    
    target_type = Column(String, nullable=False) # 'user', 'project', 'system_setting'
    target_id = Column(Integer, nullable=True)
    
    metadata_json = Column(JSON, default={})
    ip_address = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("User")
