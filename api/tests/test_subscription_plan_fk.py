"""End-to-end tests for the Subscription.plan_id FK relationship.

Exercises the new model: Subscription now points at a Plan row via plan_id
rather than carrying an enum. These tests verify:
- Subscription creation uses plan_id and joins back to the plan row
- The plan_name property resolves through the relationship
- The legacy enum column is no longer required for code that reads plans
"""
import uuid

import pytest
from sqlalchemy import create_engine as _ce
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Yield a SQLAlchemy session with only Subscription/Plan/User tables.

    These tests don't need the rest of the schema, so we create just the
    three relevant tables — that keeps the FK tests independent of the
    JSONB-on-SQLite portability issue (which is a separate item).
    """
    from app.models.base import Base

    engine = _ce("sqlite:///:memory:")
    Base.metadata.tables["plans"].create(engine, checkfirst=True)
    Base.metadata.tables["users"].create(engine, checkfirst=True)
    Base.metadata.tables["subscriptions"].create(engine, checkfirst=True)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def plans(db_session):
    """Seed the four canonical Plan rows for FK tests."""
    from app.models.plan import Plan

    existing_names = {p.name for p in db_session.query(Plan).all()}
    plan_defs = [
        ("free", 4),
        ("scheduler", 13),
        ("committed", 30),
        ("intense", 62),
    ]
    for name, vid_limit in plan_defs:
        if name not in existing_names:
            db_session.add(Plan(name=name, video_limit_monthly=vid_limit))
    db_session.commit()
    return {p.name: p for p in db_session.query(Plan).all()}


@pytest.fixture
def user(db_session):
    from app.models.user import User, UserRole

    u = User(
        id=uuid.uuid4(),
        email=f"fk-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="x",
        name="FK Test",
        role=UserRole.user,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def test_subscription_has_plan_id_column():
    """Subscription model exposes plan_id, not the legacy enum."""
    from app.models.subscription import Subscription

    assert hasattr(Subscription, "plan_id"), "Subscription.plan_id is missing"
    assert hasattr(Subscription, "plan_rel"), "Subscription.plan_rel relationship is missing"


def test_create_subscription_with_plan_id(db_session, user, plans):
    from app.models.subscription import Subscription, SubscriptionStatus

    free_plan = plans["free"]
    sub = Subscription(
        user_id=user.id,
        plan_id=free_plan.id,
        status=SubscriptionStatus.active,
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    assert sub.plan_id == free_plan.id
    assert sub.plan_name == "free"


def test_plan_name_resolves_through_relationship(db_session, user, plans):
    """plan_name joins through plan_id, not from a stale enum value."""
    from app.models.subscription import Subscription, SubscriptionStatus

    intense = plans["intense"]
    sub = Subscription(user_id=user.id, plan_id=intense.id, status=SubscriptionStatus.active)
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    assert sub.plan_name == "intense"
    # The relationship is loaded, not just an ID
    assert sub.plan_rel is not None
    assert sub.plan_rel.name == "intense"


def test_plan_name_defaults_to_free_when_null(db_session, user):
    """If a row has neither plan_id nor a legacy enum, fall back to 'free'."""
    from app.models.subscription import Subscription

    sub = Subscription(user_id=user.id, status="active")
    # plan_id is None at this point
    db_session.add(sub)
    db_session.commit()

    assert sub.plan_name == "free"


def test_upgrade_changes_plan_id(db_session, user, plans):
    """Webhook-style upgrade: switch from free to intense via plan_id."""
    from app.models.subscription import Subscription, SubscriptionStatus

    sub = Subscription(
        user_id=user.id,
        plan_id=plans["free"].id,
        status=SubscriptionStatus.active,
    )
    db_session.add(sub)
    db_session.commit()

    # Upgrade!
    sub.plan_id = plans["intense"].id
    db_session.commit()
    db_session.refresh(sub)
    assert sub.plan_name == "intense"


def test_subscription_user_relationship_still_works(db_session, user, plans):
    """Existing back-populates (Subscription.user, User.subscriptions) still load."""
    from app.models.subscription import Subscription, SubscriptionStatus

    sub = Subscription(user_id=user.id, plan_id=plans["scheduler"].id, status=SubscriptionStatus.active)
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    assert sub.user is not None
    assert sub.user.id == user.id
    assert len(user.subscriptions) >= 1