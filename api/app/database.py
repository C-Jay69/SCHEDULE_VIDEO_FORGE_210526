"""Database engine + session factory.

The engine is created lazily on first access, not at module import. This lets:
  - `alembic revision --autogenerate` work without a live Postgres connection
  - unit tests import models without needing the pool kwargs to match
  - test suites run against SQLite without monkey-patching create_engine

Backwards-compat: `from app.database import engine` still works because
`engine` is a transparent proxy that delegates to the real SQLAlchemy Engine
the first time anything on it is touched.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

_engine_lock = threading.Lock()
_engine: Optional[Engine] = None


def _build_engine() -> Engine:
    """Construct the SQLAlchemy Engine with the configured DATABASE_URL."""
    url = settings.database_url
    kwargs: dict = {}
    # Postgres-only pool kwargs — skip on SQLite so dev/test/alembic autogenerate
    # can use an in-memory DB without crashes. The trade-off is that SQLite
    # doesn't get pooling (it doesn't need it — it's local).
    if not url.startswith("sqlite"):
        kwargs.update(pool_pre_ping=True, pool_size=10, max_overflow=20)
    return create_engine(url, **kwargs)


def get_engine() -> Engine:
    """Return the lazily-initialized Engine, building it on first call."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = _build_engine()
    return _engine


def reset_engine() -> None:
    """Discard the cached Engine. Used in tests after a backend switch."""
    global _engine
    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None


class _LazyEngine:
    """Proxy that delegates every attribute access to the lazily-built Engine.

    Allows `from app.database import engine` to keep working everywhere, but
    defers the actual connection-pool creation until something touches it.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(get_engine(), name)

    def __repr__(self) -> str:
        if _engine is None:
            return "<LazyEngine: not yet initialized>"
        return repr(_engine)


engine = _LazyEngine()

Base = declarative_base()

# SessionLocal is created without a bind — the engine is attached per-session
# in get_db() so we don't trigger engine creation at import time.
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_db():
    """FastAPI dependency that yields a session bound to the lazy engine."""
    db = SessionLocal(bind=get_engine())
    try:
        yield db
    finally:
        db.close()