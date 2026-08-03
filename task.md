# VideoForge MVP — Task Tracker

## STATUS: 🟡 Local-boot ready, NOT production-deploy ready

The API now imports cleanly and the test suite passes against an in-memory
SQLite database. But several deeper issues remain before this can be safely
deployed to a real environment.

---

## Done (this audit pass)

### Phase 1 — Unblock startup
- [x] Created `api/app/models/base.py` that re-exports `Base` from `database.py`,
      so `models/__init__.py`'s `from .base import Base` resolves.
- [x] Deleted duplicate model files: `audit.py` and `system_setting.py`. The
      canonical files (`admin_audit_log.py`, `system_settings.py`) match the
      0001 migration schemas and are the ones imported by `admin.py`.
- [x] Worker Dockerfile now `COPY api/app /app/app` and sets
      `ENV PYTHONPATH=/app` so worker code can do `from app.models import X`.
- [x] Billing webhook now maps `intense → pro`, `scheduler/committed → creator`,
      else `free` — matches the actual seeded plan names.
- [x] `seed.py` is now in the api image (`/seed.py`); Makefile's `seed` target
      updated to run `python /seed.py`.
- [x] Verified billing router is mounted only once (the old "twice" note in
      the original `task.md` was wrong).

### Phase 2 — Security + hygiene
- [x] Deleted 17 junk empty files in the repo root.
- [x] Removed tracked `venv/` directory; added `venv/`/`.venv/`/`env/`/`ENV/` to `.gitignore`.
- [x] Removed stale local `.env`; rewrote `.env.example` with safe placeholders
      (no committed secrets).
- [x] Added `web/public/.gitkeep` so the web Dockerfile COPY succeeds.
- [x] CORS now reads `CORS_ALLOWED_ORIGINS` (comma-separated, whitespace-trimmed,
      deduplicated) — production deploys can set their domain.
- [x] `api/Dockerfile` defaults to production CMD (multi-worker uvicorn).
      `docker-compose.yml` sets `DEV=1` for the api service so `make up` still
      gives `--reload`.

### Phase 3 — Operate
- [x] Added `AuditLogResponse` to `schemas/__init__.py` exports.
- [x] Fixed `UsageEvent.user_id` type: was Integer FK → users.id (UUID), now
      UUID FK → users.id.
- [x] Rewrote `seed.py` to match current User, Plan, SystemSettings schemas
      (no more `full_name`/`hashed_password`/`plan_id`/`plan_name`).
- [x] Rewrote `0002_phase2_expansion` migration: removed conflicting
      `CREATE TABLE` for `system_settings` and `admin_audit_logs` (already
      exist from 0001), fixed UUID FK types in `usage_events`/`project_assets`.
- [x] Added `api/tests/test_app_startup.py` + `conftest.py` (10 tests, all pass
      against in-memory SQLite).
- [x] Added `pytest` + `pytest-asyncio` to `api/requirements.txt`.
- [x] Removed empty `api/app/services/` directory.
- [x] Imported `VideoJob` and `PublishedPost` in `models/__init__.py` so the
      metadata includes all tables.

---

## Still open — required for production deploy

These aren't showstoppers for local boot, but will block a real deploy:

1. **No HTTPS / no real secrets manager.** Fine for local, not for prod.
   Move `SECRET_KEY`, Stripe keys, MinIO keys, OAuth secrets to a manager
   (AWS Secrets Manager / Doppler / Vault).
2. **No Alembic autogenerate.** `env.py` imports `from app.database import Base`
   and `from app.models import *`, but `database.py` creates the engine at
   import time, which breaks `make model name=...`. Lazy-init the engine.
3. **No CI workflow.** Add `.github/workflows/ci.yml` running `pytest` + `ruff`.
4. **PlanType enum vs Plan.name mismatch.** `Subscription.plan` is the legacy
   `free/creator/pro` enum; seeded plans are `free/scheduler/committed/intense`.
   The billing webhook now maps the names; everywhere else that compares plan
   strings silently mismatches. Migrate `Subscription.plan` to a FK to
   `plans.id` and drop the enum.
5. **Project.settings_json uses JSONB.** Won't work on non-Postgres databases
   (breaks tests). Make it portable.
6. **No `make test` smoke target.** Add a `tests/smoke.sh` that boots the
   stack and curls `/health`.
7. **`api/app/core/storage.py` is referenced by `main.py` but unverified.**
   Read it; ensure MinIO client works in production.
8. **Web app has 0 tests.**
9. **Worker has 0 tests** (the existing `tests/integration_test_pipeline.py`
   uses outdated column names — `full_name`, `hashed_password`, `title`,
   `Plan(name="daily")` — and won't run as-is).
10. **No rate limits** on auth/billing routes.
11. **No request size limits** on the upload routes.
12. **No Sentry / structured logging** for production debugging.
13. **No backup strategy** for Postgres data + MinIO videos.
14. **`task.md` itself should probably move into `docs/` and versioned**
    once the project reaches a real release cadence.

---

## Quick verification

```bash
# In a fresh shell, with the venv activated:
cd api && python -m pytest tests/ -v
# Expect: 10 passed

# Boot the stack:
cd .. && make up && make migrate && make seed
# Expect: services start, admin user seeded, plans inserted.
```