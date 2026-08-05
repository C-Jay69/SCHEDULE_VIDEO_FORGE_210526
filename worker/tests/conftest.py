"""Pytest config for the worker test suite.

The worker imports its own modules as `worker.*`, which only works when
the repo root is on sys.path. pytest's default rootdir + conftest discovery
already takes care of that when running `pytest` from the repo root, but
when running from inside worker/ we have to do it ourselves.

Also patches create_engine so the worker's lazy DB engine accepts the
sqlite URLs the tests use.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Default test environment
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

# Strip Postgres-only pool kwargs from create_engine when targeting sqlite.
import sqlalchemy  # noqa: E402

_real_create_engine = sqlalchemy.create_engine


def _patched_create_engine(url, **kwargs):
    if isinstance(url, str) and url.startswith("sqlite"):
        for k in ("pool_size", "max_overflow", "pool_pre_ping"):
            kwargs.pop(k, None)
    return _real_create_engine(url, **kwargs)


sqlalchemy.create_engine = _patched_create_engine
