"""Custom middleware: maintenance mode + structured request logging."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Cache the maintenance flag so we don't hit the DB on every request.
_MAINT_CACHE_TTL = 10  # seconds
_maint_state: dict = {"enabled": False, "checked_at": 0.0}


def _maintenance_enabled() -> bool:
    now = time.monotonic()
    if now - _maint_state["checked_at"] > _MAINT_CACHE_TTL:
        enabled = False
        try:
            from ..database import SessionLocal, get_engine
            from ..models.system_settings import SystemSettings

            db = SessionLocal(bind=get_engine())
            try:
                row = db.query(SystemSettings).filter(SystemSettings.key == "maintenance_mode").first()
                enabled = row is not None and row.value == "true"
            finally:
                db.close()
        except Exception as exc:  # DB unavailable — assume not in maintenance
            logger.debug("maintenance check skipped: %s", exc)
        _maint_state.update({"enabled": enabled, "checked_at": now})
    return _maint_state["enabled"]


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _maintenance_enabled():
            return await call_next(request)

        # Always allow health checks + docs so infra can probe the app.
        if request.url.path in ("/health", "/api/health", "/ready", "/openapi.json", "/docs", "/redoc"):
            return await call_next(request)

        # Allow admin actions (admins should be able to toggle maintenance off).
        if request.url.path.startswith("/api/admin"):
            return await call_next(request)

        return JSONResponse(
            status_code=503,
            content={"detail": "VideoForge is in maintenance mode. Please try again later."},
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s -> %s (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
