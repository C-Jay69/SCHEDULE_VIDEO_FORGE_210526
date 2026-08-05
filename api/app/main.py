import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.secrets import populate_environ

# Pull secrets from the configured backend BEFORE pydantic-settings reads env
# vars. In dev (SECRETS_BACKEND unset) this is a no-op.
populate_environ()

from .config import settings
from .core.middleware import MaintenanceModeMiddleware, RequestLoggingMiddleware
from .core.storage import ensure_bucket_exists
from .database import SessionLocal, engine
from .routers import (
    admin,
    auth,
    billing,
    oauth,
    projects,
    published,
    schedules,
    social,
    templates,
    users,
    videos,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("VideoForge API starting up...")
    try:
        ensure_bucket_exists()
        logger.info("MinIO bucket ready")
    except Exception as e:
        logger.warning(f"MinIO not ready: {e}")
    yield
    # Shutdown
    logger.info("VideoForge API shutting down...")


app = FastAPI(
    title="VideoForge API",
    version="1.0.0",
    description="Video content scheduling SaaS API",
    lifespan=lifespan,
)

# CORS — defaults to next_public_app_url + localhost, plus anything in CORS_ALLOWED_ORIGINS
# Dedupe so the same origin never appears twice.
seen = set()
cors_origins = []
for origin in [settings.next_public_app_url, "http://localhost:3000"]:
    if origin and origin not in seen:
        cors_origins.append(origin)
        seen.add(origin)
if settings.cors_allowed_origins:
    for o in (raw.strip() for raw in settings.cors_allowed_origins.split(",")):
        if o and o not in seen:
            cors_origins.append(o)
            seen.add(o)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Maintenance mode + request logging. Order matters: maintenance first so
# it short-circuits before logging.
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MaintenanceModeMiddleware)

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(oauth.router, prefix="/api")
app.include_router(social.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(published.router, prefix="/api")
app.include_router(templates.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "videoforge-api"}


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "service": "videoforge-api"}


@app.get("/ready")
async def ready():
    """Readiness probe: verifies DB connectivity."""
    from sqlalchemy import text

    issues = []
    try:
        db = SessionLocal(bind=engine)
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:
        issues.append(f"database: {exc}")

    return JSONResponse(
        status_code=200 if not issues else 503,
        content={"status": "ready" if not issues else "not_ready", "issues": issues},
    )
