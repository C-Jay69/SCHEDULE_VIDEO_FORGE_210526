"""Smoke tests for the VideoForge API.

These tests verify the FastAPI app boots, all routers mount, and the public
endpoints (health, OpenAPI docs) respond. They do NOT require a database —
the lifespan startup runs without DB calls (MinIO connection is wrapped in
a try/except in main.py).
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Build a TestClient. This triggers FastAPI lifespan startup."""
    from app.main import app  # imported lazily so env vars are set first
    with TestClient(app) as c:
        yield c


def test_app_imports():
    """The app module loads without raising."""
    from app.main import app
    assert app.title == "VideoForge API"
    assert app.version == "1.0.0"


def test_health_endpoint(client):
    """GET /health returns 200 with status=ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "videoforge-api"


def test_api_health_endpoint(client):
    """GET /api/health returns 200 (the route Next.js proxies through)."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_schema_loads(client):
    """The OpenAPI schema is generated and includes all routers."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    # Each router group should expose at least one path
    expected_prefixes = [
        "/api/auth",
        "/api/projects",
        "/api/videos",
        "/api/schedules",
        "/api/oauth",
        "/api/billing",
        "/api/admin",
    ]
    paths = list(schema["paths"].keys())
    for prefix in expected_prefixes:
        assert any(p.startswith(prefix) for p in paths), (
            f"No path starts with {prefix!r}. "
            f"Have: {[p for p in paths if '/api/' in p]}"
        )


def test_docs_endpoint(client):
    """Swagger UI is reachable."""
    r = client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower()


def test_redoc_endpoint(client):
    """ReDoc UI is reachable."""
    r = client.get("/redoc")
    assert r.status_code == 200


def test_cors_allows_configured_origins():
    """The CORS middleware is wired with at least the dev defaults."""
    from app.main import cors_origins
    assert "http://localhost:3000" in cors_origins
    assert len(cors_origins) >= 1


def test_models_register_all_tables():
    """All SQLAlchemy models register their tables on metadata."""
    from app.models import Base
    tables = set(Base.metadata.tables.keys())
    expected = {
        "users", "subscriptions", "projects", "videos", "video_jobs",
        "schedules", "published_posts", "social_accounts",
        "system_settings", "admin_audit_logs",
        "plans", "usage_events", "project_assets", "prompt_templates",
    }
    missing = expected - tables
    assert not missing, f"Models not registered: {missing}"


def test_no_duplicate_admin_audit_log_model():
    """Only one AdminAuditLog class is defined."""
    from app.models.admin_audit_log import AdminAuditLog as Canonical
    from app.models import AdminAuditLog as Imported
    # Same class — same module
    assert Canonical is Imported


def test_seed_module_imports():
    """seed.py imports without error (offline check)."""
    import importlib.util
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "x" * 40)
    spec = importlib.util.spec_from_file_location(
        "seed", os.path.join(os.path.dirname(__file__), "..", "..", "seed.py")
    )
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    assert hasattr(seed, "main")
    assert hasattr(seed, "seed_plans")
    assert hasattr(seed, "seed_admin")