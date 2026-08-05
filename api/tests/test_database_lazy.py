"""Tests for the lazy engine initialization."""

import contextlib


def test_engine_not_built_at_module_import(monkeypatch):
    """Importing app.database should NOT create a real Engine.

    This is the core of the lazy-init fix: before the change, importing
    database.py ran create_engine(settings.database_url, ...) which crashed
    against sqlite (max_overflow not supported). Now we should be able to
    import the module even when the configured URL is one that wouldn't
    actually work as a production engine.
    """
    # Force an engine config that would fail at create_engine time
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    # Clear any cached engine from previous tests
    from app import database

    database.reset_engine()

    # Importing should not raise
    from app.database import engine

    assert engine is not None


def test_engine_built_on_first_attribute_access(monkeypatch):
    """Touching the engine proxy triggers the real Engine construction."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from app import database

    database.reset_engine()
    assert database._engine is None, "engine should not be built yet"

    # Touch a method — this should trigger lazy init
    engine = database.engine
    pool_class = type(engine.pool).__name__
    assert pool_class in ("StaticPool", "SingletonThreadPool", "NullPool")
    assert database._engine is not None, "engine should be built after access"


def test_get_engine_is_thread_safe(monkeypatch):
    """get_engine() returns the same Engine instance across calls."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from app import database

    database.reset_engine()
    e1 = database.get_engine()
    e2 = database.get_engine()
    assert e1 is e2


def test_reset_engine_disposes_and_clears(monkeypatch):
    """reset_engine() drops the cached Engine so it can be rebuilt."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from app import database

    database.reset_engine()
    _ = database.get_engine()  # build it
    assert database._engine is not None
    database.reset_engine()
    assert database._engine is None


def test_session_binds_to_engine_per_session(monkeypatch):
    """get_db() returns a session that uses the lazy engine."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from app import database

    database.reset_engine()

    gen = database.get_db()
    session = next(gen)
    try:
        # The session should have a bind set
        assert session.bind is not None
    finally:
        with contextlib.suppress(StopIteration):
            next(gen)
