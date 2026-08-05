"""Shared pytest fixtures and patches for the API test suite.

The app uses SQLAlchemy with Postgres-specific pool kwargs (pool_size,
max_overflow, pool_pre_ping). When tests run against sqlite:///:memory:
those kwargs aren't accepted. This conftest patches create_engine so the
test suite can use a SQLite URL without modifying the application code.
"""

import os

# Always run against SQLite so the suite works without a Postgres server and
# without depending on the ambient DATABASE_URL (CI injects a Postgres URL that
# would otherwise win here and change engine pooling behavior in
# test_database_lazy). The app's `settings` singleton is created lazily on the
# first `from app.config import settings`, which happens after this module is
# imported — so a hard assignment below is picked up reliably.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "x" * 40)
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import sqlalchemy

_real_create_engine = sqlalchemy.create_engine


def _patched_create_engine(url, **kwargs):
    """Strip Postgres-only pool kwargs when running against sqlite."""
    if isinstance(url, str) and url.startswith("sqlite"):
        for k in ("pool_size", "max_overflow", "pool_pre_ping"):
            kwargs.pop(k, None)
    return _real_create_engine(url, **kwargs)


sqlalchemy.create_engine = _patched_create_engine


# (no global db_session fixture here — see test_subscription_plan_fk.py for
# a narrowly-scoped fixture that only creates the tables needed by the FK
# tests, sidestepping the JSONB-on-SQLite issue.)
