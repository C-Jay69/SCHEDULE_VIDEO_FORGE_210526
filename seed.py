"""
Idempotent seed script — run after migrations.
Creates: admin user, test user, plans (free/scheduler/committed/intense), system settings.

Usage:
    python seed.py
    ADMIN_EMAIL=me@co.com ADMIN_PASSWORD=secret python seed.py
"""

import os
import sys
from datetime import datetime, timezone

# Allow importing api models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/videoforge")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@videoforge.io")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123!")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@videoforge.io")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpass123!")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

from api.models.user import User
from api.models.plan import Plan
from api.models.settings import SystemSetting
from api.db import Base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def seed_plans(db):
    plans = [
        {
            "name": "free",
            "display_name": "Free",
            "price_monthly_cents": 0,
            "price_yearly_cents": 0,
            "videos_per_month": 4,
            "motion_credits": 0,
            "posts_per_week": 1,
            "auto_publish": False,
            "watermark": True,
            "hd_resolution": False,
            "background_music": False,
            "voice_cloning": False,
            "edit_preview": False,
            "stripe_price_id_monthly": None,
            "stripe_price_id_yearly": None,
        },
        {
            "name": "scheduler",
            "display_name": "Scheduler",
            "price_monthly_cents": 1500,
            "price_yearly_cents": 1200,
            "videos_per_month": 13,  # ~3/week
            "motion_credits": 27,
            "posts_per_week": 3,
            "auto_publish": True,
            "watermark": False,
            "hd_resolution": True,
            "background_music": True,
            "voice_cloning": True,
            "edit_preview": True,
            "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_SCHEDULER_MONTHLY"),
            "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_SCHEDULER_YEARLY"),
        },
        {
            "name": "committed",
            "display_name": "Committed",
            "price_monthly_cents": 3000,
            "price_yearly_cents": 2500,
            "videos_per_month": 30,  # once/day
            "motion_credits": 62,
            "posts_per_week": 7,
            "auto_publish": True,
            "watermark": False,
            "hd_resolution": True,
            "background_music": True,
            "voice_cloning": True,
            "edit_preview": True,
            "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_COMMITTED_MONTHLY"),
            "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_COMMITTED_YEARLY"),
        },
        {
            "name": "intense",
            "display_name": "Intense",
            "price_monthly_cents": 5500,
            "price_yearly_cents": 4600,
            "videos_per_month": 62,  # twice/day
            "motion_credits": 124,
            "posts_per_week": 14,
            "auto_publish": True,
            "watermark": False,
            "hd_resolution": True,
            "background_music": True,
            "voice_cloning": True,
            "edit_preview": True,
            "stripe_price_id_monthly": os.getenv("STRIPE_PRICE_INTENSE_MONTHLY"),
            "stripe_price_id_yearly": os.getenv("STRIPE_PRICE_INTENSE_YEARLY"),
        },
    ]

    for p in plans:
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
        existing.role = "admin"
        existing.is_active = True
        print(f"  [UPDATE] admin: {ADMIN_EMAIL}")
    else:
        plan = db.query(Plan).filter(Plan.name == "free").first()
        admin = User(
            email=ADMIN_EMAIL,
            full_name="Admin",
            hashed_password=pwd_ctx.hash(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            plan_id=plan.id if plan else None,
            plan_name="free",
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
    plan = db.query(Plan).filter(Plan.name == "committed").first()
    user = User(
        email=TEST_USER_EMAIL,
        full_name="Test User",
        hashed_password=pwd_ctx.hash(TEST_USER_PASSWORD),
        role="user",
        is_active=True,
        plan_id=plan.id if plan else None,
        plan_name="committed",
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    print(f"  [CREATE] test user: {TEST_USER_EMAIL}")


def seed_system_settings(db):
    defaults = [
        ("max_video_retries", "3", "Max Celery retries per video job"),
        ("video_expiry_days", "30", "Days before video files are deleted"),
        ("watermark_text", "VideoForge", "Text shown on free plan watermarks"),
        ("max_free_videos", "4", "Max videos for free plan per month"),
        ("maintenance_mode", "false", "Set to 'true' to block new jobs"),
        ("openai_model", "gpt-4o", "OpenAI model used for script generation"),
        ("tts_voice", "alloy", "Default TTS voice (OpenAI)"),
    ]
    for key, value, description in defaults:
        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if existing:
            print(f"  [SKIP] setting: {key}")
        else:
            db.add(SystemSetting(
                key=key,
                value=value,
                description=description,
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
