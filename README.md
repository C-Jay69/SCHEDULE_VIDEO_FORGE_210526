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
| AI | Ollama (llama3.2 scripts), Piper TTS, faster-whisper, FFmpeg |
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

## Step-by-Step Deployment Guide

### 1. Clone & Configure Environment

```bash
git clone <repository-url>
cd videoforge-mvp
make setup        # copies .env.example → .env
```

### 2. Configure Environment Variables

Edit the `.env` file and set at minimum:

```dotenv
# Required: Generate a secure random string (use: openssl rand -hex 32)
SECRET_KEY=your_long_random_secret_key_here

# Required: Stripe configuration (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Required: Admin credentials
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure_admin_password

# Optional but recommended: YouTube API (for auto-publishing)
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret

# Optional: OpenRouter for fallback text generation (free models)
# Get free key from https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-your_openrouter_key
```

### 3. Start All Services

```bash
make up           # Builds and starts all Docker containers
make migrate      # Applies database migrations
make seed         # Creates admin user, plans, and system settings
```

### 4. Verify Deployment

The platform will be available at:
- **Main Application** → http://localhost:3000
- **API Documentation** → http://localhost:8000/docs
- **Admin Panel** → http://localhost:3000/admin (login with credentials from .env)

### 5. Optional Integrations

#### Stripe Payments (Enable Subscription Features)
1. Create products in Stripe Dashboard matching plan names:
   - Scheduler ($15/month)
   - Committed ($30/month) 
   - Intense ($55/month)
2. Add price IDs to `.env`:
   ```
   STRIPE_PRICE_SCHEDULER_MONTHLY=price_from_stripe
   STRIPE_PRICE_SCHEDULER_YEARLY=price_from_stripe
   STRIPE_PRICE_COMMITTED_MONTHLY=price_from_stripe
   STRIPE_PRICE_COMMITTED_YEARLY=price_from_stripe
   STRIPE_PRICE_INTENSE_MONTHLY=price_from_stripe
   STRIPE_PRICE_INTENSE_YEARLY=price_from_stripe
   ```
3. Configure webhook in Stripe Dashboard pointing to `https://yourdomain.com/api/webhooks/stripe`

#### YouTube Auto-Publishing
1. Create Google Cloud Project
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Web Application)
4. Set credentials in `.env` and add authorized redirect URI: `http://localhost:8000/api/oauth/youtube/callback`

### 6. Managing Services

```bash
# View all logs
make logs

# View specific service logs
make logs-web     # Frontend (Next.js)
make logs-api     # Backend (FastAPI)  
make logs-worker  # Video generation worker

# Stop all services
make down

# Restart services
make restart

# Rebuild after code changes
make up --build
```

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
                                    Ollama/Piper/Whisper → FFmpeg → S3
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
| `OLLAMA_BASE_URL` | Ollama service URL (default: http://ollama:11434) |
| `OLLAMA_MODEL` | Ollama model to use (default: llama3.2) |
| `OPENROUTER_API_KEY` | Optional: OpenRouter API key for free model fallback |
| `OPENROUTER_MODEL` | OpenRouter model (default: meta-llama/llama-3.1-8b-instruct:free) |
| `PIPER_MODEL_PATH` | Path to Piper TTS model (default: /app/models/en_US-lessac-medium.onnx) |
| `WHISPER_MODEL_SIZE` | Whisper model size (default: base) |
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
