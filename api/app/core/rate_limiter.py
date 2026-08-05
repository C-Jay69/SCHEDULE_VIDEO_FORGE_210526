"""Simple in-memory rate limiter for auth/billing endpoints.

Production note: a single-process in-memory limiter is sufficient for the
API's default single-node deployment. If you scale the API horizontally,
swap this for a Redis-backed limiter (Redis is already in the stack).
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)

# Limits: (requests, window_seconds)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "auth": (10, 60),  # 10 auth attempts per minute
    "billing": (30, 60),  # 30 billing calls per minute
    "default": (120, 60),
}


def get_client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(namespace: str = "default"):
    """FastAPI dependency: enforce a sliding-window rate limit."""

    async def _dependency(request: Request):
        limit, window = RATE_LIMITS.get(namespace, RATE_LIMITS["default"])
        key = f"{namespace}:{get_client_key(request)}"
        now = time.monotonic()

        with _lock:
            bucket = _hits[key]
            # Drop entries older than the window
            while bucket and bucket[0] < now - window:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(status_code=429, detail="Too many requests, please slow down")
            bucket.append(now)

    return _dependency
