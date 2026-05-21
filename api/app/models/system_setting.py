from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    value_type = Column(String, default="string") # 'string', 'int', 'bool', 'json'
    description = Column(String, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
