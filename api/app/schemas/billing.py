from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlanResponse(BaseModel):
    name: str
    price_cents: int
    stripe_price_id: Optional[str] = None
    video_limit_monthly: int
    motion_credits_monthly: int
    storage_limit_gb: int
    features: List[str] = Field(..., alias="features_json")

    class Config:
        from_attributes = True
        populate_by_name = True


class CheckoutRequest(BaseModel):
    plan: str  # The name of the plan from the DB (e.g., "scheduler", "daily")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    period_end: Optional[datetime] = None

    class Config:
        from_attributes = True
