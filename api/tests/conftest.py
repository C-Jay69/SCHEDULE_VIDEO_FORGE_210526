"""Shared pytest fixtures and patches for the API test suite.

The app uses SQLAlchemy with Postgres-specific pool kwargs (pool_size,
max_overflow, pool_pre_ping). When tests run against sqlite:///:memory:
those kwargs aren't accepted. This conftest patches create_engine so the
test suite can use a SQLite URL without modifying the application code.
"""
import os

# Default to sqlite for the test DB so tests run without a Postgres server
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
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