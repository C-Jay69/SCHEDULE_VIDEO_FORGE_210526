import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..core.rate_limiter import rate_limit
from ..core.security import get_current_user
from ..database import get_db
from ..models.addon_grant import AddonGrant
from ..models.billing_event import BillingEvent
from ..models.plan import Plan
from ..models.subscription import Subscription, SubscriptionStatus
from ..models.user import User
from ..models.webhook_event import WebhookEvent
from ..schemas.billing import AddonCheckoutRequest, CheckoutRequest, PlanResponse, SubscriptionResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["billing"])
stripe.api_key = settings.stripe_secret_key

# One-time add-on products. price_env is the config attr holding the Stripe
# price ID; add-ons with an empty price ID are omitted from the catalog and
# rejected at checkout until they're configured.
ADDON_CATALOG = {
    "motion_credits": {
        "label": "50 AI-Visual Credits",
        "price_env": "stripe_addon_motion_price_id",
        "price_cents": 1500,
    },
    "voice_cloning": {
        "label": "Voice Cloning Pack (10 videos)",
        "price_env": "stripe_addon_voice_cloning_price_id",
        "price_cents": 1900,
    },
    "brand_kit": {
        "label": "Brand Kit (custom intro/outro)",
        "price_env": "stripe_addon_brand_kit_price_id",
        "price_cents": 500,
    },
}


def _get_or_create_customer(db: Session, user: User) -> str:
    """Return the user's Stripe customer, creating and persisting one if absent."""
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(email=user.email, metadata={"user_id": str(user.id)})
    user.stripe_customer_id = customer.id
    db.add(user)
    db.commit()
    return customer.id


@router.get("/billing/plans", response_model=list[PlanResponse])
async def get_plans(db: Session = Depends(get_db)):
    """Fetch all available plans from the database."""
    plans = db.query(Plan).filter(Plan.is_active.is_(True)).all()
    return plans


@router.post("/billing/checkout")
async def create_checkout(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("billing")),
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
        customer_id = _get_or_create_customer(db, current_user)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={"user_id": str(current_user.id), "plan_name": plan.name},
        )
        return {"checkout_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/billing/addons")
async def list_addons():
    """Catalog of purchasable one-time add-ons (only those with a Stripe price)."""
    return [
        {"key": key, "label": item["label"], "price_cents": item["price_cents"]}
        for key, item in ADDON_CATALOG.items()
        if getattr(settings, item["price_env"])
    ]


@router.post("/billing/checkout/addon")
async def create_addon_checkout(
    data: AddonCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("billing")),
):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=400, detail="Stripe not configured")

    product = ADDON_CATALOG.get(data.product_key)
    if not product:
        raise HTTPException(status_code=400, detail="Unknown add-on")

    price_id = getattr(settings, product["price_env"])
    if not price_id:
        raise HTTPException(status_code=400, detail="Add-on not configured for Stripe")

    quantity = max(1, data.quantity or 1)
    success_url = data.success_url or f"{settings.next_public_app_url}/settings?billing=success"
    cancel_url = data.cancel_url or f"{settings.next_public_app_url}/settings"

    try:
        customer_id = _get_or_create_customer(db, current_user)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": quantity}],
            mode="payment",
            success_url=success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "kind": "addon",
                "product_key": data.product_key,
                "quantity": str(quantity),
            },
        )
        return {"checkout_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/billing/addon-grants")
async def get_addon_grants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    grants = (
        db.query(AddonGrant)
        .filter(AddonGrant.user_id == current_user.id)
        .order_by(AddonGrant.created_at.desc())
        .all()
    )
    return [
        {
            "product_key": g.product_key,
            "quantity": g.quantity,
            "created_at": g.created_at,
            "expires_at": g.expires_at,
        }
        for g in grants
    ]


@router.get("/billing/portal")
@router.post("/billing/portal")
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
        # Return both shapes so both GET and POST callers can destructure.
        return {"portal_url": session.url, "url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/billing/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")

    return SubscriptionResponse(
        id=str(sub.id),
        plan=sub.plan_name,
        status=sub.status.value if hasattr(sub.status, "value") else str(sub.status),
        period_end=sub.period_end,
    )


def _persist_webhook(db: Session, event) -> None:
    payload = event.get("data", {}).get("object", {})
    wh = WebhookEvent(
        provider="stripe",
        event_id=event.get("id"),
        event_type=event.get("type"),
        payload_json=payload,
        processed=False,
    )
    db.add(wh)
    db.flush()
    return wh


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload") from None
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature") from None

    # Persist the raw event so admins can inspect delivery history.
    webhook_event = _persist_webhook(db, event)
    event_type = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        session = obj
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")

        if metadata.get("kind") == "addon":
            # One-time add-on purchase: credit the user's grant, no plan change.
            user = db.query(User).filter(User.id == user_id).first() if user_id else None
            product_key = metadata.get("product_key")
            if user and product_key:
                try:
                    quantity = int(metadata.get("quantity", "1"))
                except (TypeError, ValueError):
                    quantity = 1
                db.add(AddonGrant(user_id=user.id, product_key=product_key, quantity=quantity))
                db.add(
                    BillingEvent(
                        user_id=user.id,
                        stripe_event_id=event.get("id"),
                        event_type="addon.purchased",
                        amount_cents=session.get("amount_total"),
                        metadata_json={"product_key": product_key, "quantity": quantity},
                    )
                )
        else:
            plan_name = metadata.get("plan_name")
            stripe_sub_id = session.get("subscription")
            if user_id and plan_name:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    db_plan = db.query(Plan).filter(Plan.name == plan_name).first()
                    if not db_plan:
                        logger.error(f"Webhook error: Plan {plan_name} not found in DB")
                        webhook_event.error_message = f"Plan {plan_name} not found"
                        db.commit()
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
                    db.add(
                        BillingEvent(
                            user_id=user.id,
                            stripe_event_id=event.get("id"),
                            event_type="checkout.session.completed",
                            metadata_json={"plan": plan_name},
                        )
                    )

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        stripe_sub = obj
        sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == stripe_sub["id"]).first()
        if sub:
            status_map = {
                "active": SubscriptionStatus.active,
                "canceled": SubscriptionStatus.canceled,
                "past_due": SubscriptionStatus.past_due,
                "trialing": SubscriptionStatus.trialing,
                "incomplete": SubscriptionStatus.incomplete,
            }
            sub.status = status_map.get(stripe_sub["status"], SubscriptionStatus.canceled)
            if stripe_sub.get("current_period_end"):
                sub.period_end = datetime.fromtimestamp(stripe_sub["current_period_end"], tz=timezone.utc)
            db.add(
                BillingEvent(
                    user_id=sub.user_id,
                    stripe_event_id=event.get("id"),
                    event_type=event_type,
                    metadata_json={"stripe_subscription_id": stripe_sub["id"]},
                )
            )

    elif event_type in ("invoice.payment_succeeded", "invoice.payment_failed"):
        invoice = obj
        sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == invoice.get("subscription")).first()
        if sub:
            if event_type == "invoice.payment_failed":
                sub.status = SubscriptionStatus.past_due
            db.add(
                BillingEvent(
                    user_id=sub.user_id,
                    stripe_event_id=event.get("id"),
                    event_type=event_type,
                    amount_cents=invoice.get("amount_due"),
                    metadata_json={"invoice_id": invoice.get("id")},
                )
            )

    webhook_event.processed = True
    webhook_event.processed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "ok"}
