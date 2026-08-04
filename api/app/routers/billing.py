from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import stripe
from ..database import get_db
from ..models.user import User
from ..models.subscription import Subscription, SubscriptionStatus
from ..models.plan import Plan
from ..schemas.billing import PlanResponse, CheckoutRequest, SubscriptionResponse
from ..core.security import get_current_user
from ..config import settings
from typing import List
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(tags=["billing"])
stripe.api_key = settings.stripe_secret_key

@router.get("/billing/plans", response_model=List[PlanResponse])
async def get_plans(db: Session = Depends(get_db)):
    """Fetch all available plans from the database."""
    plans = db.query(Plan).all()
    return plans


@router.post("/billing/checkout")
async def create_checkout(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=400, detail="Stripe not configured")

    # Find the plan in the DB by name
    plan = db.query(Plan).filter(Plan.name == data.plan).first()
    if not plan or not plan.stripe_price_id:
        raise HTTPException(status_code=400, detail="Invalid plan or plan not configured for Stripe")

    success_url = data.success_url or f"{settings.next_public_app_url}/settings?billing=success"
    cancel_url = data.cancel_url or f"{settings.next_public_app_url}/pricing"

    try:
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={"user_id": str(current_user.id), "plan_name": plan.name},
        )
        return {"checkout_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/billing/portal")
async def billing_portal(
    current_user: User = Depends(get_current_user),
):
    if not settings.stripe_secret_key or not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Billing portal not available")

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.next_public_app_url}/settings",
        )
        return {"portal_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan_name = session.get("metadata", {}).get("plan_name")
        stripe_sub_id = session.get("subscription")

        if user_id and plan_name:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Find the Plan row to attach to this subscription via FK
                db_plan = db.query(Plan).filter(Plan.name == plan_name).first()
                if not db_plan:
                    logger.error(f"Webhook error: Plan {plan_name} not found in DB")
                    return {"status": "plan_not_found"}

                sub = (
                    db.query(Subscription)
                    .filter(Subscription.user_id == user.id)
                    .order_by(Subscription.created_at.desc())
                    .first()
                )

                if sub:
                    sub.plan_id = db_plan.id
                    sub.status = SubscriptionStatus.active
                    sub.stripe_subscription_id = stripe_sub_id
                else:
                    new_sub = Subscription(
                        user_id=user.id,
                        plan_id=db_plan.id,
                        status=SubscriptionStatus.active,
                        stripe_subscription_id=stripe_sub_id,
                    )
                    db.add(new_sub)
                db.commit()

    elif event["type"] in ("customer.subscription.updated", "customer.subscription.deleted"):
        stripe_sub = event["data"]["object"]
        sub = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == stripe_sub["id"])
            .first()
        )
        if sub:
            status_map = {
                "active": SubscriptionStatus.active,
                "canceled": SubscriptionStatus.canceled,
                "past_due": SubscriptionStatus.past_due,
                "trialing": SubscriptionStatus.trialing,
            }
            sub.status = status_map.get(stripe_sub["status"], SubscriptionStatus.canceled)
            if stripe_sub.get("current_period_end"):
                from datetime import datetime
                sub.period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
            db.commit()

    return {"status": "ok"}
