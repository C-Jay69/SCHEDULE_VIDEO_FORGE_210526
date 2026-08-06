import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"
    trialing = "trialing"
    incomplete = "incomplete"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stripe_subscription_id = Column(String(255), nullable=True)
    # plan_id points at the Plan table (migration 0003 dropped the legacy
    # `plan` enum column — keep the model in sync so ORM SELECTs don't break).
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active, nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="subscriptions")
    plan_rel = relationship("Plan", back_populates="subscriptions")

    @property
    def plan_name(self) -> str:
        """Return the active plan name (e.g. 'starter', 'pro')."""
        if self.plan_rel is not None:
            return self.plan_rel.name
        return "starter"
