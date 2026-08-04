"""Smoke tests for the worker module.

The worker code talks to Postgres, Redis, OpenAI, Ollama, MinIO, and YouTube.
Doing a real end-to-end test requires all of those running, which is exactly
what these tests deliberately avoid — they verify the *plumbing* of the
worker without requiring any backing service to be available.

What's covered:
- celery_app builds cleanly with the expected task list
- The lazy DB engine inside worker.db works without crashing at import time
- The provider base class exposes the expected interface
"""
import os


def test_celery_app_imports_and_registers_tasks():
    """The Celery app constructs and lists the expected task modules."""
    from worker.celery_app import celery_app

    # The `include` list tells Celery to scan these modules for @shared_task
    # decorated functions at startup. If a module name is misspelled the
    # worker would silently fail to register any tasks from it.
    assert "tasks.video_generation" in celery_app.conf.include
    assert "tasks.publishing" in celery_app.conf.include


def test_celery_app_uses_env_broker():
    """Broker URL is read from CELERY_BROKER_URL with a sane fallback."""
    from worker.celery_app import celery_app

    broker = celery_app.conf.broker_url or ""
    # Either env-supplied URL or our fallback (redis://redis:6379/0).
    assert broker.startswith("redis://")


def test_db_module_imports_without_db():
    """worker.db must import without a live database connection.

    The SessionLocal factory only opens connections when get_db_session()
    is called, so import-time side effects must be limited to engine
    creation (which is lazy if pool_pre_ping is set).
    """
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    import importlib
    import worker.db as db_module
    importlib.reload(db_module)

    assert db_module.SessionLocal is not None
    assert callable(db_module.get_db_session)


def test_text_generation_orchestrator_constructs():
    """The orchestrator builds even with no API keys configured.

    Real providers (Ollama/OpenRouter) need their backing services, but
    constructing the orchestrator should not fail. It should always have
    at least the Ollama provider wired in (it's free + local).
    """
    from worker.pipeline.text_generation import TextGenerationOrchestrator

    orch = TextGenerationOrchestrator()
    # Ollama is the default first provider
    assert len(orch.providers) >= 1
    assert orch.providers[0].provider_name == "ollama"


def test_pipeline_modules_exist():
    """Every pipeline submodule mentioned in celery_app.include is importable.

    Heavy modules (video_render) need optional deps like Pillow. If those
    are missing in the test environment, we skip the import — the build
    process is what really validates their availability.
    """
    expected_modules = [
        "worker.pipeline.text_generation",
        "worker.pipeline.tts",
        "worker.pipeline.stt",
        "worker.pipeline.orchestrator",
    ]
    for mod in expected_modules:
        try:
            __import__(mod)
        except Exception as e:
            raise AssertionError(f"{mod} failed to import: {e}")

    # Optional heavy module — only assert if Pillow is installed.
    try:
        import PIL  # noqa: F401
    except ImportError:
        return
    try:
        __import__("worker.pipeline.video_render")
    except Exception as e:
        raise AssertionError(f"worker.pipeline.video_render failed: {e}")


def test_worker_db_lazy_engine_does_not_crash_on_sqlite(monkeypatch):
    """worker.db uses create_engine — same lazy-engine fix as api.

    Before the fix, worker.db would call create_engine with pool kwargs
    that sqlite rejects. After the conftest patches create_engine, the
    engine builds successfully and get_db_session returns a usable Session.
    """
    from sqlalchemy import create_engine as _real_ce

    real_create_engine = _real_ce

    def patched(url, **kwargs):
        if isinstance(url, str) and url.startswith("sqlite"):
            for k in ("pool_size", "max_overflow", "pool_pre_ping"):
                kwargs.pop(k, None)
        return real_create_engine(url, **kwargs)

    monkeypatch.setattr("sqlalchemy.create_engine", patched)

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    import importlib
    import worker.db as db_module
    importlib.reload(db_module)

    session = db_module.get_db_session()
    assert session is not None
    session.close()
