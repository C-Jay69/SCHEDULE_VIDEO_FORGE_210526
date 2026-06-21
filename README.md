# VideoForge MVP

AI-powered video generation and social media autopublishing platform.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS, Recharts |
| API | FastAPI, SQLAlchemy, Alembic, Pydantic v2 |
| Worker | Celery + Redis (Beat for scheduling) |
| Database | PostgreSQL |
| Auth | JWT (access + refresh tokens) |
| Payments | Stripe Checkout + Billing Portal |
| Storage | S3-compatible (MinIO for local dev) |
| AI | OpenAI (GPT-4o scripts, TTS voices) |
| Social | YouTube OAuth v2 auto-publish; Instagram/TikTok/X metadata export |

---

## Plans

| Plan | Price | Posts |
|---|---|---|
| **Free** | $0 | 1 video total, watermark |
| **Scheduler** | $15/mo | 3×/week, 27 motion credits |
| **Committed** | $30/mo | Once/day, 62 motion credits |
| **Intense** | $55/mo | Twice/day, 124 motion credits |

---

## Quick Start

### 1. Clone & configure

```bash
git clone <repo>
cd videoforge-mvp
make setup        # copies .env.example → .env
```

Edit `.env` — at minimum set:

```dotenv
SECRET_KEY=<long-random-string>
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
ADMIN_EMAIL=you@yourdomain.com
ADMIN_PASSWORD=supersecret
```

### 2. Start everything

```bash
make up           # builds & starts all containers
make migrate      # runs Alembic migrations
make seed         # seeds plans, admin user, system settings
```

App is running at:
- **Web** → http://localhost:3000
- **API docs** → http://localhost:8000/docs
- **API redoc** → http://localhost:8000/redoc

### 3. Connect Stripe (optional for payments)

1. Create products in Stripe Dashboard matching plan names
2. Add price IDs to `.env`:
   ```
   STRIPE_PRICE_SCHEDULER_MONTHLY=price_xxx
   STRIPE_PRICE_SCHEDULER_YEARLY=price_xxx
   STRIPE_PRICE_COMMITTED_MONTHLY=price_xxx
   STRIPE_PRICE_COMMITTED_YEARLY=price_xxx
   STRIPE_PRICE_INTENSE_MONTHLY=price_xxx
   STRIPE_PRICE_INTENSE_YEARLY=price_xxx
   ```
3. Set up Stripe webhook pointing to `https://yourdomain.com/api/webhooks/stripe`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`

### 4. Connect YouTube (optional)

1. Create a project in Google Cloud Console
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials → Web Application
4. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
5. Add `http://localhost:3000/api/auth/callback/youtube` to authorized redirect URIs

---

## Common Commands

```bash
make logs           # tail all container logs
make logs-api       # api logs only
make logs-worker    # worker logs only

make migrate        # apply new migrations
make model name="add_avatar_url"  # generate migration from model changes

make seed           # re-run seed (idempotent)

make test           # run pytest
make lint           # ruff + next lint

make psql           # drop into postgres shell
make redis-cli      # drop into redis shell

make shell-api      # bash in api container
make shell-worker   # bash in worker container

make down           # stop all containers
make clean          # stop + remove volumes (destructive!)
```

---

## Project Structure

```
videoforge-mvp/
├── api/                    # FastAPI application
│   ├── core/               # Config, security, dependencies
│   ├── models/             # SQLAlchemy ORM models
│   ├── routers/            # API route handlers
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic
│   └── main.py
├── worker/                 # Celery worker
│   ├── pipeline/           # Video generation pipeline steps
│   │   ├── script.py       # GPT-4o script generation
│   │   ├── tts.py          # Text-to-speech
│   │   ├── visuals.py      # Image/motion generation
│   │   ├── editor.py       # FFmpeg composition
│   │   └── uploader.py     # S3 + social publishing
│   ├── tasks/              # Celery task definitions
│   ├── celery_app.py
│   └── db.py
├── web/                    # Next.js frontend
│   ├── app/
│   │   ├── (marketing)/    # Public pages (landing, pricing)
│   │   ├── (auth)/         # Login, register
│   │   ├── (app)/          # Authenticated app pages
│   │   └── admin/          # Admin panel
│   ├── components/
│   │   ├── ui/             # Shadcn-style primitives
│   │   └── layout/         # Navbar
│   ├── hooks/              # useAuth
│   └── lib/                # api client, auth, utils
├── migrations/             # Alembic migration files
├── docker-compose.yml
├── seed.py
├── Makefile
└── README.md
```

---

## Architecture

```
Browser → Next.js (3000) → /api/* proxy → FastAPI (8000)
                                                ↓
                                          PostgreSQL
                                          Redis (task queue)
                                                ↓
                                        Celery Worker
                                                ↓
                                    OpenAI → FFmpeg → S3
                                                ↓
                                    YouTube API / metadata export
```

**Celery queues:**
- `priority` — Pro/Intense users
- `default` — all others

**Beat tasks:**
- `process_scheduled` — every 5 min, triggers due scheduled posts

---

## Environment Variables

See `.env.example` for full list. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key — must be long & random |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `OPENAI_API_KEY` | GPT-4o + TTS |
| `STRIPE_SECRET_KEY` | Stripe payments |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification |
| `AWS_ACCESS_KEY_ID` | S3/MinIO storage |
| `AWS_SECRET_ACCESS_KEY` | S3/MinIO storage |
| `S3_BUCKET_NAME` | Video storage bucket |
| `GOOGLE_CLIENT_ID` | YouTube OAuth |
| `GOOGLE_CLIENT_SECRET` | YouTube OAuth |
| `ADMIN_EMAIL` | Seeded admin account |
| `ADMIN_PASSWORD` | Seeded admin password |

---

## Admin Panel

Access at `/admin` — requires user with `role = "admin"`.

Seeded admin: `$ADMIN_EMAIL` / `$ADMIN_PASSWORD`

Features:
- Metrics dashboard (users, MRR, videos, job queue)
- User table — search, deactivate, promote to admin
- Job queue — retry failed jobs
- System settings — key/value editor
- Audit logs — filterable action log

---

## Notes

- **Non-YouTube platforms** (Instagram, TikTok, X): VideoForge exports a `.zip` with the video file + caption/metadata text. No scraping, no unofficial APIs.
- **Watermarks**: Free plan videos get an overlay burned in by FFmpeg.
- **Storage**: Videos are stored in S3 (or MinIO locally). Download URLs are pre-signed S3 URLs.
- **Social tokens**: YouTube OAuth tokens are encrypted at rest using Fernet (key derived from `SECRET_KEY`).
