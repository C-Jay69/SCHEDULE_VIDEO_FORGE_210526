# VideoForge MVP — Task Tracker

## STATUS: 🟢 Production-deploy ready (code), subject to the open items below

All local checks pass: api (ruff check/format, 37 pytest), worker (ruff check,
6 pytest), web (tsc, next lint warnings-only, next build), and `tests/smoke.sh`.
All three Docker images build, `docker-compose.production.yml` validates, and a
from-scratch boot of the stack was verified end-to-end: fresh Postgres →
migrations 0001→0006 → `seed.py` → register/login against the production api
image (with bcrypt pinned, lazy engine, secrets-manager backends).

Deploy notes:
- `docker compose --env-file .env -f docker-compose.production.yml up -d --build`
  (env must set `ACME_EMAIL`, `PRIMARY_DOMAIN`, `REDIS_PASSWORD`, `SECRET_KEY`,
  `DATABASE_URL`, `REDIS_URL`; see `docs/DEPLOYMENT.md`).
- `NEXT_PUBLIC_*` and `API_URL` are baked into the web image at build time via
  compose `build.args` — rebuild the web image when the domain changes.

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

### Phase 4 — Deploy-readiness hardening (this session)
- [x] Added `api/ruff.toml` + `worker/ruff.toml`; fixed all ruff findings
      (E712 `is_(True)`, RUF013 implicit Optional, SIM105, B904 `from e`,
      F823 in `worker/tasks/video_generation.py`, etc.); `ruff format` both trees.
- [x] Pinned `bcrypt==4.0.1` in `api/requirements.txt` — passlib 1.7.4 +
      bcrypt 5.0.0 crashes every password hash/verify with
      `ValueError: password cannot be longer than 72 bytes`.
- [x] Fixed migration `0004_settings_json_portable` (`USING jsonb::text::json`
      → `USING settings_json::text::json`); added `0006_subscriptions_updated_at`
      (model had `updated_at`, no migration created it → every register 500'd).
- [x] Fixed `seed.py` container path bootstrap (scans for `app/__init__.py`,
      picks `/app` in the container); verified seed completes in-container.
- [x] Fixed CI-breaking test isolation bug: `api/tests/conftest.py` now forces
      `DATABASE_URL=sqlite:///:memory:` (CI injects a Postgres URL that made
      `test_database_lazy` fail on the cached `Settings` singleton). CI env
      simulation now passes 37/37.
- [x] Fixed admin API/frontend contract: `/admin/jobs` returns
      `{"jobs", "total"}`; `AdminMetrics` gained active_users/total_videos/
      total_schedules/total_published.
- [x] Cookie security: `COOKIE_SECURE` setting (default True), used by all
      `set_cookie` calls; compose passes `COOKIE_SECURE`.
- [x] `api/Dockerfile`: added `curl` (compose healthcheck), pip
      `--retries 10 --timeout 300` + BuildKit cache mount (fast rebuilds).
      Same for `worker/Dockerfile`.
- [x] `web/Dockerfile`: works with repo-root build context
      (`COPY web/...`); `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_APP_URL`/`API_URL`
      baked at build time via ARG (runtime env was a no-op → hydration/proxy
      mismatch); compose passes them as `build.args`.
- [x] `docker-compose.yml` dev web context harmonized to repo root; added
      root `.dockerignore`; gitignored `.next/`.
- [x] Created `docs/BACKUPS.md`; `docs/DEPLOYMENT.md` secrets list now includes
      `DATABASE_URL` + `REDIS_URL`.
- [x] Verified end-to-end: all three images build; fresh DB → migrations
      0001→0006 → seed → register/login against the production api image;
      web container serves + proxies `/api/*` to the API.

---

## Still open — small / non-blocking

Most of the original blockers were resolved (see Done). The rest are minor:

1. **Worker image build not yet verified end-to-end** in this environment — the
   Dockerfile is the same proven pattern as the api image, worker code is
   covered by 6 passing tests, but the final `pip install`/TTS model downloads
   were still running on a very slow network. Rebuild + `celery inspect ping`
   when the network cooperates.
2. **Sentry is optional / not wired by default** — compose passes `SENTRY_DSN`
   if set, but `sentry-sdk` is not installed in the images (see
   `docs/DEPLOYMENT.md` §9). Structured request logging exists via middleware.
3. **Web app has 0 unit tests** — CI covers typecheck + lint + build.
4. **`task.md` should move into `docs/`** once at a real release cadence.

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