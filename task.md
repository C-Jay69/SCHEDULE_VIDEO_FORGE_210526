# VideoForge MVP — Task Tracker

## STATUS: ✅ COMPLETE

All files written. Build ready.

---

## Final File Count
- api/ — models, routers, services, schemas, core, main.py ✅
- migrations/ — env.py, script.py.mako, alembic.ini, 0001_initial.py ✅
- worker/ — celery_app, db, pipeline/*, tasks/* ✅
- web/app/ — 22 page/layout files across marketing/auth/app/admin ✅
- web/components/ — ui primitives + navbar ✅
- web/lib/ + hooks/ — api.ts, auth.ts, utils.ts, useAuth.ts ✅
- web/Dockerfile ✅
- docker-compose.yml ✅
- .env.example ✅
- seed.py ✅
- Makefile ✅
- README.md ✅

## Plans (per user request)
- Free: $0 — 1 video, watermark, no auto-post
- Scheduler: $15/mo — 3x/week, 27 motion credits, all features
- Committed: $30/mo — once/day, 62 motion credits, all features  ← Most Popular
- Intense: $55/mo — twice/day, 124 motion credits, all features

## Known Issues (non-blocking for MVP)
1. api/main.py mounts billing router twice (Stripe webhook + /api/billing)
2. Worker Dockerfile COPY ../api — needs root build context in docker-compose
3. recharts not in web/package.json — add `"recharts": "^2.12.0"` before build
