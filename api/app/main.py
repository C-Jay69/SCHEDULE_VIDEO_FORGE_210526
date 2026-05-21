from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import engine, Base
from .routers import auth, projects, videos, schedules, oauth, billing, admin
from .core.storage import ensure_bucket_exists

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.next_public_app_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(oauth.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "videoforge-api"}


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "service": "videoforge-api"}
