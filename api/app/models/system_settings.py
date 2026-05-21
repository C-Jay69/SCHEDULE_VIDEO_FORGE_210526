from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from ..database import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
