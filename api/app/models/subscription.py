from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from ..database import Base


class PlanType(str, enum.Enum):
    """Legacy plan identifier — used only to backfill plan_id on existing rows.

    New code should use the Plan table via Subscription.plan_id. The enum is
    kept here so the migration can read old values and the existing schema
    works on a database that hasn't been migrated yet.
    """

    free = "free"
    creator = "creator"
    pro = "pro"


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
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    # `plan` enum kept deprecated for one migration window. After 0003 runs
    # and any existing rows are populated, the column is dropped.
    plan = Column(Enum(PlanType), nullable=True)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.active, nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")
    plan_rel = relationship("Plan", back_populates="subscriptions")

    @property
    def plan_name(self) -> str:
        """Return the active plan name (e.g. 'free', 'intense').

        Order of precedence:
        1. The live Plan row joined via plan_id (preferred).
        2. The legacy enum column (read-only fallback for old rows).
        3. 'free' as a safe default if both are unset.
        """
        if self.plan_rel is not None:
            return self.plan_rel.name
        if self.plan is not None:
            return self.plan.value
        return "free"
