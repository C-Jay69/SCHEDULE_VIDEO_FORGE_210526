import logging
from datetime import timedelta

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..core.rate_limiter import rate_limit
from ..core.security import (
    create_access_token,
    decode_token,
    get_current_user,
    get_password_hash,
    settings,
    verify_password,
)
from ..database import get_db
from ..models.plan import Plan
from ..models.subscription import Subscription, SubscriptionStatus
from ..models.user import User, UserRole
from ..schemas.auth import (
    ChangePasswordRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: UserRegister,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("auth")),
):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        name=data.name,
        role=UserRole.user,
    )
    db.add(user)
    db.flush()

    # Create Stripe customer
    try:
        customer = stripe.Customer.create(email=data.email, name=data.name)
        user.stripe_customer_id = customer.id
    except Exception:
        pass  # Non-fatal, stripe may not be configured

    # Create free subscription — look up the free Plan row to set plan_id
    free_plan = db.query(Plan).filter(Plan.name == "free").first()
    if free_plan is None:
        # Make registration resilient on an unseeded DB by creating the
        # canonical free plan on the fly.
        free_plan = Plan(
            name="free",
            video_limit_monthly=settings.free_videos_per_month,
            storage_limit_gb=1,
            motion_credits_monthly=0,
            features_json=[],
            price_cents=0,
            is_active=True,
        )
        db.add(free_plan)
        db.flush()
    sub = Subscription(
        user_id=user.id,
        plan_id=free_plan.id,
        status=SubscriptionStatus.active,
    )
    db.add(sub)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 7,
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("auth")),
):
    user = db.query(User).filter(User.email == data.email, User.is_active.is_(True)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 7,
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    current_user = await get_current_user(request, db)
    token = create_access_token({"sub": str(current_user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 7,
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(current_user))


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.post("/reset-password/request", response_model=MessageResponse)
async def reset_password_request(
    data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("auth")),
):
    """Issue a password-reset token.

    If SMTP is configured the token is emailed; otherwise (dev) the token is
    returned so the flow can be exercised end-to-end without a mail server.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # Don't reveal whether an email exists.
        return MessageResponse(message="If that email exists, a reset link has been sent.")

    reset_token = create_access_token(
        {"sub": str(user.id), "purpose": "password_reset"},
        expires_delta=timedelta(hours=1),
    )

    smtp_from = getattr(settings, "smtp_from", "") or ""
    if smtp_from and getattr(settings, "smtp_host", ""):
        try:
            from ..services.email_service import send_password_reset_email

            await send_password_reset_email(user.email, reset_token)
        except Exception as exc:
            logger.warning("failed to send reset email: %s", exc)
    else:
        logger.info("password reset token for %s: %s", user.email, reset_token)

    return MessageResponse(message="If that email exists, a reset link has been sent.")


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def reset_password_confirm(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    payload = decode_token(data.token)
    if not payload or payload.get("purpose") != "password_reset" or not payload.get("sub"):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return MessageResponse(message="Password updated. You can now sign in.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return MessageResponse(message="Password changed successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
