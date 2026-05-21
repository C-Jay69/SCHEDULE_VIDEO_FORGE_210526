from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from ..database import get_db
from ..models.user import User, UserRole
from ..models.subscription import Subscription, PlanType, SubscriptionStatus
from ..schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from ..core.security import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, settings
)
import stripe

router = APIRouter(prefix="/auth", tags=["auth"])

stripe.api_key = settings.stripe_secret_key


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister, response: Response, db: Session = Depends(get_db)):
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

    # Create free subscription
    sub = Subscription(
        user_id=user.id,
        plan=PlanType.free,
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
        secure=False,
        max_age=60 * 60 * 24 * 7,
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 7,
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
