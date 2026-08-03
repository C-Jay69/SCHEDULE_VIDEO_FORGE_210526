"""
Idempotent seed script — run after migrations.

Seeds: admin user, test user, plans (free/scheduler/committed/intense),
default system settings.

Runs either:
- inside the api container: `python /seed.py`
- on the host (from repo root): `python seed.py`
Both add the appropriate path so the api models import correctly.

Env vars:
    DATABASE_URL       Postgres connection string
    ADMIN_EMAIL        Admin email (default: admin@videoforge.local)
    ADMIN_PASSWORD     Admin password (default: change-me-locally)
    TEST_USER_EMAIL    Test user email
    TEST_USER_PASSWORD Test user password
"""

import os
import sys
from datetime import datetime, timezone


def _bootstrap_path():
    """Put the api package on sys.path no matter where this script is run."""
    here = os.path.dirname(os.path.abspath(__file__))
    # Running inside the container: api code is at /app
    if os.path.isdir(os.path.join(here, "app")):
        sys.path.insert(0, here)
    # Running from the host repo root: api code is at api/
    elif os.path.isdir(os.path.join(here, "api", "app")):
        sys.path.insert(0, os.path.join(here, "api"))
    else:
        # Last resort: assume cwd is the repo root and api/ is a sibling
        sys.path.insert(0, os.path.join(os.getcwd(), "api"))


_bootstrap_path()

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://videoforge:videoforge_secret@postgres:5432/videoforge",
)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@videoforge.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-locally")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@videoforge.local")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpass123!")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.models.user import User, UserRole  # noqa: E402
from app.models.plan import Plan  # noqa: E402
from app.models.system_settings import SystemSettings  # noqa: E402

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


# Plan definitions aligned with the Plan model schema.
# Feature flags are stored in features_json; price is a single cents value.
PLAN_DEFS = [
    {
        "name": "free",
        "stripe_price_id": os.getenv("STRIPE_FREE_PRICE_ID"),
        "video_limit_monthly": 4,
        "storage_limit_gb": 1,
        "motion_credits_monthly": 0,
        "features_json": ["watermark"],
        "price_cents": 0,
        "is_active": True,
    },
    {
        "name": "scheduler",
        "stripe_price_id": os.getenv("STRIPE_SCHEDULER_PRICE_ID"),
        "video_limit_monthly": 13,  # ~3/week
        "storage_limit_gb": 10,
        "motion_credits_monthly": 27,
        "features_json": ["no_watermark", "auto_publish", "hd", "background_music"],
        "price_cents": 1500,
        "is_active": True,
    },
    {
        "name": "committed",
        "stripe_price_id": os.getenv("STRIPE_COMMITTED_PRICE_ID"),
        "video_limit_monthly": 30,  # once/day
        "storage_limit_gb": 50,
        "motion_credits_monthly": 62,
        "features_json": ["no_watermark", "auto_publish", "hd", "background_music", "voice_cloning"],
        "price_cents": 3000,
        "is_active": True,
    },
    {
        "name": "intense",
        "stripe_price_id": os.getenv("STRIPE_INTENSE_PRICE_ID"),
        "video_limit_monthly": 62,  # twice/day
        "storage_limit_gb": 200,
        "motion_credits_monthly": 124,
        "features_json": [
            "no_watermark", "auto_publish", "hd", "background_music",
            "voice_cloning", "priority_queue",
        ],
        "price_cents": 5500,
        "is_active": True,
    },
]


SETTING_DEFAULTS = [
    ("max_video_retries", "3"),
    ("video_expiry_days", "30"),
    ("watermark_text", "VideoForge"),
    ("max_free_videos", "4"),
    ("maintenance_mode", "false"),
    ("openai_model", "gpt-4o"),
    ("tts_voice", "alloy"),
]


def seed_plans(db):
    for p in PLAN_DEFS:
        existing = db.query(Plan).filter(Plan.name == p["name"]).first()
        if existing:
            for k, v in p.items():
                setattr(existing, k, v)
            print(f"  [UPDATE] plan: {p['name']}")
        else:
            db.add(Plan(**p))
            print(f"  [CREATE] plan: {p['name']}")
    db.commit()


def seed_admin(db):
    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing:
        existing.role = UserRole.admin
        existing.is_active = True
        print(f"  [UPDATE] admin: {ADMIN_EMAIL}")
    else:
        admin = User(
            email=ADMIN_EMAIL,
            password_hash=pwd_ctx.hash(ADMIN_PASSWORD),
            name="Admin",
            role=UserRole.admin,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        print(f"  [CREATE] admin: {ADMIN_EMAIL}")
    db.commit()


def seed_test_user(db):
    existing = db.query(User).filter(User.email == TEST_USER_EMAIL).first()
    if existing:
        print(f"  [SKIP] test user already exists: {TEST_USER_EMAIL}")
        return
    user = User(
        email=TEST_USER_EMAIL,
        password_hash=pwd_ctx.hash(TEST_USER_PASSWORD),
        name="Test User",
        role=UserRole.user,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    print(f"  [CREATE] test user: {TEST_USER_EMAIL}")


def seed_system_settings(db):
    for key, value in SETTING_DEFAULTS:
        existing = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if existing:
            print(f"  [SKIP] setting: {key}")
        else:
            db.add(SystemSettings(
                key=key,
                value=value,
                updated_at=datetime.now(timezone.utc),
            ))
            print(f"  [CREATE] setting: {key}")
    db.commit()


def main():
    print("=== VideoForge Seed ===\n")
    db = SessionLocal()
    try:
        print("→ Seeding plans…")
        seed_plans(db)

        print("\n→ Seeding admin user…")
        seed_admin(db)

        print("\n→ Seeding test user…")
        seed_test_user(db)

        print("\n→ Seeding system settings…")
        seed_system_settings(db)

        print("\n✓ Seed complete.")
    except Exception as e:
        db.rollback()
        print(f"\n✗ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()