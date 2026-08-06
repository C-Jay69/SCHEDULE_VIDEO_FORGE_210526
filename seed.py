"""
Idempotent seed script — run after migrations.

Seeds: admin user, test user, plans (starter/creator/pro/agency),
default system settings.

Runs either:
- inside the api container: `python /seed.py`
- on the host (from repo root): `python seed.py`
Both add the appropriate path so the api models import correctly.

Env vars:
    DATABASE_URL       Postgres connection string
    ADMIN_EMAIL        Admin email (default: admin@videoforge.io)
    ADMIN_PASSWORD     Admin password (default: change-me-locally)
    TEST_USER_EMAIL    Test user email
    TEST_USER_PASSWORD Test user password
"""

import os
import sys
from datetime import datetime, timezone


def _bootstrap_path():
    """Put the api package on sys.path no matter where this script is run.

    Looks for a directory that contains an `app/__init__.py` package in:
      • the api container (/app, when seed.py lives at /seed.py)
      • the host repo root (api/app)
      • the host api/ dir, or cwd
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    if here and here != "/":
        candidates.append(here)
    candidates.extend(
        [
            os.path.join(here, "app"),  # container: /app
            os.path.join(here, "api"),  # host repo root
            os.path.join(os.getcwd(), "api"),
        ]
    )
    for candidate in candidates:
        if os.path.isfile(os.path.join(candidate, "app", "__init__.py")):
            sys.path.insert(0, candidate)
            return
    # Last resort: assume cwd is the repo root and api/ is a sibling.
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
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@videoforge.io")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-locally")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@videoforge.io")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpass123!")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _env_or_none(name):
    """Return the env var as-is, or None if unset/blank.

    Stripe price IDs are a unique nullable column; empty strings would collide
    across plans ('' != NULL), so blank env vars must become NULL.
    """
    value = os.getenv(name, "").strip()
    return value or None

from app.models.user import User, UserRole  # noqa: E402
from app.models.plan import Plan  # noqa: E402
from app.models.system_settings import SystemSettings  # noqa: E402

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


# Plan definitions aligned with the Plan model schema.
# Feature flags are stored in features_json; price is a single cents value.
PLAN_DEFS = [
    {
        "name": "starter",
        "stripe_price_id": _env_or_none("STRIPE_STARTER_PRICE_ID"),
        "video_limit_monthly": 3,
        "storage_limit_gb": 1,
        "motion_credits_monthly": 0,
        "features_json": ["watermark"],
        "price_cents": 0,
        "is_active": True,
    },
    {
        "name": "creator",
        "stripe_price_id": _env_or_none("STRIPE_CREATOR_PRICE_ID"),
        "video_limit_monthly": 25,
        "storage_limit_gb": 10,
        "motion_credits_monthly": 50,
        "features_json": ["no_watermark", "auto_publish", "hd", "background_music"],
        "price_cents": 1900,
        "is_active": True,
    },
    {
        "name": "pro",
        "stripe_price_id": _env_or_none("STRIPE_PRO_PRICE_ID"),
        "video_limit_monthly": 100,
        "storage_limit_gb": 100,
        "motion_credits_monthly": 200,
        "features_json": [
            "no_watermark", "auto_publish", "hd", "background_music",
            "voice_cloning", "priority_queue",
        ],
        "price_cents": 4900,
        "is_active": True,
    },
    {
        "name": "agency",
        "stripe_price_id": _env_or_none("STRIPE_AGENCY_PRICE_ID"),
        "video_limit_monthly": 500,
        "storage_limit_gb": 500,
        "motion_credits_monthly": 1000,
        "features_json": [
            "no_watermark", "auto_publish", "hd", "background_music",
            "voice_cloning", "priority_queue", "white_label", "api_access",
        ],
        "price_cents": 14900,
        "is_active": True,
    },
]


# Tolerate rows created by earlier seeds/migrations under the old tier names.
# Renaming in place (rather than inserting new rows) keeps plan IDs stable so
# existing subscriptions keep pointing at the correct tier.
PLAN_RENAMES = {
    "free": "starter",
    "scheduler": "creator",
    "committed": "pro",
    "intense": "agency",
}


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
        if not existing:
            old_name = next((o for o, n in PLAN_RENAMES.items() if n == p["name"]), None)
            if old_name:
                existing = db.query(Plan).filter(Plan.name == old_name).first()
                if existing:
                    existing.name = p["name"]
                    print(f"  [RENAME] plan: {old_name} -> {p['name']}")
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