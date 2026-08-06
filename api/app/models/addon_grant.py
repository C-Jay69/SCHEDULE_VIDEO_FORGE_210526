import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..database import Base


class AddonGrant(Base):
    """A one-time add-on purchase credited to a user.

    product_key is one of the add-on catalog keys (e.g. "motion_credits",
    "voice_cloning", "brand_kit"). quantity is the number of units purchased
    (e.g. credit packs). expires_at is optional for time-boxed grants.
    """

    __tablename__ = "addon_grants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_key = Column(String(64), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
