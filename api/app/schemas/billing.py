from datetime import datetime

from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    name: str
    price_cents: int
    stripe_price_id: str | None = None
    video_limit_monthly: int
    motion_credits_monthly: int
    storage_limit_gb: int
    features: list[str] = Field(..., alias="features_json")

    class Config:
        from_attributes = True
        populate_by_name = True


class CheckoutRequest(BaseModel):
    plan: str  # The name of the plan from the DB (e.g., "creator", "pro")
    success_url: str | None = None
    cancel_url: str | None = None


class AddonCheckoutRequest(BaseModel):
    product_key: str  # One of the add-on catalog keys, e.g. "motion_credits"
    quantity: int = 1
    success_url: str | None = None
    cancel_url: str | None = None


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    status: str
    period_end: datetime | None = None

    class Config:
        from_attributes = True
