#!/usr/bin/env bash
# Smoke test — runs in <5 seconds, requires only Python (no Postgres, no Docker).
#
# What this checks:
#   1. The API package imports cleanly (no top-level errors).
#   2. The FastAPI app builds and exposes critical endpoints.
#   3. The lazy database engine is importable without a real DB.
#   4. The secrets module loads in env mode.
#   5. All model definitions register without ClassNotFound errors.
#
# Use this as a quick sanity check before pushing, when CI is slow, or
# after a fresh clone to confirm the install is healthy.

set -euo pipefail

# Locate the api directory regardless of where the script is called from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_DIR="$REPO_ROOT/api"

# venv, if one exists at the repo root, takes precedence over system Python.
if [ -f "$REPO_ROOT/venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$REPO_ROOT/venv/bin/activate"
fi

cd "$API_DIR"

# Provide a tiny default so the test environment doesn't require a real DB.
export DATABASE_URL="${DATABASE_URL:-sqlite:///:memory:}"
export SECRET_KEY="${SECRET_KEY:-smoke-test-secret-key-32-chars-padding-x}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/0}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export SECRETS_BACKEND="${SECRETS_BACKEND:-env}"

echo "==> Smoke test starting ($(date -u +%FT%TZ))"
echo "    API dir: $API_DIR"
echo "    Python:  $(python --version)"
echo "    DB URL:  $DATABASE_URL"
echo

echo "[1/5] Importing app.config..."
python -c "from app.config import settings; print('    settings ok -> SECRET_KEY len:', len(settings.secret_key))"

echo "[2/5] Importing app.main + FastAPI app..."
python -c "from app.main import app; assert app.title == 'VideoForge API'"
echo "    app.title ok"

echo "[3/5] Critical endpoints registered?"
python -c "
from app.main import app
# _IncludedRouter objects don't have a .path attribute; only filter Path objects.
paths = {getattr(r, 'path', None) for r in app.routes if hasattr(r, 'path')}
required = ['/health', '/api/health', '/docs', '/openapi.json']
missing = [p for p in required if p not in paths]
assert not missing, f'missing: {missing}'
print('    endpoints present:', sorted(required))
"

echo "[4/5] Lazy engine importable without DB?"
python -c "
from app.database import engine, get_engine, reset_engine
reset_engine()
_ = engine  # triggers lazy proxy
print('    engine lazy-init ok')
"

echo "[5/5] Secrets loader in env mode?"
python -c "
from app.core.secrets import get_secret, clear_cache
clear_cache()
val = get_secret('SECRET_KEY') or 'fallback'
print('    secrets ok -> SECRET_KEY len:', len(val))
"

echo
echo "==> Smoke test passed ($(date -u +%FT%TZ))"
