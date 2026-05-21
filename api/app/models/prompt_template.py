from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, default="short-form") # e.g., 'short-form', 'long-form', 'branding'
    
    # Templates for different parts of the generation
    script_template = Column(String, nullable=False)
    title_template = Column(String, nullable=True)
    description_template = Column(String, nullable=True)
    hashtag_template = Column(String, nullable=True)
    
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
