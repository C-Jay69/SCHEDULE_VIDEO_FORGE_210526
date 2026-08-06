# VideoForge

AI-powered video generation and social media autopublishing platform.

Generate scripted, narrated, captioned short-form videos from a single topic,
then schedule them to publish to YouTube — automatically. Video visuals are
rendered with real AI footage (Magic Hour), with a static-gradient fallback
when no AI key is configured.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS, Recharts |
| API | FastAPI, SQLAlchemy, Alembic, Pydantic v2 |
| Worker | Celery + Redis (Beat for scheduling) |
| Database | PostgreSQL |
| Auth | JWT (access + refresh tokens), HTTP-only cookies |
| Payments | Stripe Checkout + Billing Portal |
| Storage | S3-compatible (MinIO for local dev) |
| AI text | Ollama (local) or OpenRouter / OpenAI (script + metadata) |
| AI audio | Piper TTS (voiceover), Whisper (auto-captions) |
| AI video | Magic Hour (optional — audio-to-video AI visuals) |
| Social | YouTube OAuth v2 auto-publish; Instagram/TikTok/X metadata export |

---

## Features

- **AI video generation pipeline** — script → voiceover → AI visuals (Magic
  Hour) → burned-in captions → upload. Fully async via Celery.
- **Auto-publishing** — schedule videos and publish to YouTube automatically;
  other platforms get an exportable `.zip` package.
- **Plan-based limits** — monthly video quotas and motion credits per plan.
  **Admins are exempt** from all paywalls (unlimited videos, no watermark, no
  YouTube auto-publish restriction).
- **Admin panel** — metrics, user management, job queue, system settings,
  audit logs.

---

## Plans

| Plan | Price | Videos/month | Motion credits | Notes |
|---|---|---|---|---|
| **Free** | $0 | 4 | 0 | Watermarked |
| **Scheduler** | $15/mo | 13 | 27 | ~3×/week, no watermark, auto-publish |
| **Committed** | $30/mo | 30 | 62 | Once/day, voice cloning |
| **Intense** | $55/mo | 62 | 124 | Twice/day, priority queue |

Plan rows are seeded into the `plans` table and enforce the monthly video
limit on `/videos/generate`. **Admin users bypass all plan limits.**

---

## Quick Start (local development)

### 1. Clone & configure

```bash
git clone <repo>
cd videoforge-mvp
make setup          # copies .env.example → .env
```

Edit `.env` — at minimum set a strong secret:

```dotenv
SECRET_KEY=<long-random-string>      # run: python -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_EMAIL=you@yourdomain.com
ADMIN_PASSWORD=change-this
```

Optional integrations (leave blank to skip):

```dotenv
OPENAI_API_KEY=sk-...                # cloud text model (else local Ollama)
MAGIC_HOUR_API_KEY=mhk_live_...      # AI video visuals (else gradient background)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. Start everything

```bash
make up           # builds & starts all containers (api, web, worker, beat,
                  # postgres, redis, minio, ollama)
make migrate      # runs Alembic migrations
make seed         # seeds plans, admin user, system settings (idempotent)
```

App is running at:

- **Web** → http://localhost:3000
- **API docs** → http://localhost:8011/docs
- **API redoc** → http://localhost:8011/redoc

> **Note on ports:** the API runs on **8011** (not 8000) to avoid clashing
> with other local services. The web proxies `/api/*` to it automatically.

> **Note on Ollama:** if you already run Ollama on the host, the container's
> `ollama` service does not publish port `11434` to the host — the worker
> reaches it over the internal Docker network. No action needed.

### 3. Connect Stripe (optional — required for paid plans)

1. Create products in Stripe Dashboard matching the plan names.
2. Add the price IDs to `.env`:
   ```
   STRIPE_STARTER_PRICE_ID=price_xxx
   STRIPE_CREATOR_PRICE_ID=price_xxx
   STRIPE_PRO_PRICE_ID=price_xxx
   STRIPE_AGENCY_PRICE_ID=price_xxx
   ```
3. Point a Stripe webhook at `https://yourdomain.com/api/webhooks/stripe`
   listening for: `checkout.session.completed`, `customer.subscription.updated`,
   `customer.subscription.deleted`, `invoice.payment_failed`.
4. Re-run `make seed` to attach the price IDs to the seeded plans.

### 4. Connect YouTube (optional — enables auto-publish)

1. Create a project in Google Cloud Console.
2. Enable the YouTube Data API v3.
3. Create OAuth 2.0 credentials → Web Application.
4. Set `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` in `.env`.
5. Add `http://localhost:3000/api/auth/callback/youtube` to the authorized
   redirect URIs (use your real domain in production).

### 5. Connect Magic Hour (optional — AI video visuals)

1. Generate an API key at https://magichour.ai/developer.
2. Set `MAGIC_HOUR_API_KEY=mhk_live_...` in `.env`.
3. The worker will now render AI footage from your voiceover (audio-to-video)
   instead of the static gradient background.

> **Costs:** every video generation consumes Magic Hour credits (charged per
> rendered frame). If credits run out or the API errors, the worker logs a
> warning and falls back to the gradient render — videos are never lost.

---

## Common Commands

```bash
make logs           # tail all container logs
make logs-api       # api logs only
make logs-worker    # worker logs only

make migrate        # apply new migrations
make model name="add_avatar_url"  # generate migration from model changes

make seed           # re-run seed (idempotent)

make test           # run pytest (in-container)
make test-fast      # run pytest directly (no Docker, uses venv)
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
│   ├── core/               # Config, security, dependencies, middleware
│   ├── models/             # SQLAlchemy ORM models
│   ├── routers/            # API route handlers (auth, users, videos, ...)
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic
│   └── main.py             # FastAPI entrypoint
├── worker/                 # Celery worker
│   ├── tasks/              # Celery task definitions
│   │   ├── video_generation.py   # Full pipeline orchestrator
│   │   └── publishing.py         # Scheduled publishing task
│   ├── pipeline/           # Pipeline steps
│   │   ├── text_generation.py    # Script + metadata (Ollama/OpenRouter)
│   │   ├── tts.py                # Piper voiceover
│   │   ├── stt.py                # Whisper auto-captions
│   │   ├── magichour.py          # Magic Hour AI visuals (optional)
│   │   ├── video_render.py       # FFmpeg assembly (captions/watermark)
│   │   ├── orchestrator.py       # Social publishing coordinator
│   │   ├── connectors/           # YouTube/Instagram/TikTok/X connectors
│   │   └── providers/            # ollama, openrouter, thumbnail
│   ├── celery_app.py       # Celery + Beat configuration
│   └── db.py
├── web/                    # Next.js frontend
│   ├── app/
│   │   ├── (marketing)/    # Public pages (landing, pricing)
│   │   ├── (auth)/         # Login, register
│   │   ├── (app)/          # Authenticated app pages
│   │   └── admin/          # Admin panel
│   ├── components/         # ui/ (shadcn-style) + layout/
│   ├── hooks/              # useAuth
│   └── lib/                # api client, auth, utils
├── docs/                   # DEPLOYMENT.md, BACKUPS.md
├── migrations/             # Alembic migration files
├── docker-compose.yml      # Local dev stack
├── docker-compose.production.yml
├── Caddyfile               # Production reverse proxy / TLS
├── seed.py                 # Idempotent seed script
├── Makefile
└── README.md
```

---

## Architecture

```
Browser → Next.js (3000) → /api/* proxy → FastAPI (8011)
                                                ↓
                                          PostgreSQL
                                          Redis (task queue)
                                                ↓
                                          Celery Worker
                                                ↓
        Ollama/OpenRouter → Piper TTS → Whisper → [Magic Hour AI visuals] → FFmpeg → S3
                                                                                    ↓
                                                            YouTube API / metadata export
```

**Video generation pipeline** (runs in the worker, one job per video):

1. **Script** — generate narration + metadata from the topic (Ollama/OpenRouter).
2. **Voiceover** — Piper TTS synthesizes the narration audio.
3. **Captions** — Whisper transcribes the audio into an SRT subtitle file.
4. **Visuals** — *optional* Magic Hour audio-to-video renders AI footage synced
   to the voiceover. Falls back to a static gradient if unconfigured/failed.
5. **Assembly** — FFmpeg burns captions (+ watermark on free plan) and
   normalizes to 9:16 1080×1920.
6. **Storage** — upload to S3/MinIO; download URLs are pre-signed.
7. **Publish** — auto-publish to YouTube if scheduled, else export package.

**Celery queues:**

- `priority` — Pro / Agency plan users
- `default` — everyone else

**Beat tasks:**

- `process_scheduled` — every 5 minutes, fires due scheduled posts.

---

## Environment Variables

See `.env.example` for the full annotated list. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key — must be long & random |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis + Celery |
| `APP_URL` | Canonical URL of the API (default `http://localhost:8011`) |
| `NEXT_PUBLIC_API_URL` | Browser-facing API base URL |
| `OPENAI_API_KEY` / `OPENROUTER_API_KEY` | Cloud text models (optional) |
| `OLLAMA_BASE_URL` | Local LLM endpoint |
| `MAGIC_HOUR_API_KEY` | AI video visuals (optional) |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe payments |
| `STRIPE_*_PRICE_ID` | Plan price IDs (starter/creator/pro/agency) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `S3_BUCKET_NAME` | S3/MinIO |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | YouTube OAuth |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Seeded admin account |
| `SECRETS_BACKEND` | `env` (default) / `file` / `aws` |

---

## Admin Panel

Access at `/admin` (or the **Admin** link in the nav when signed in as an
admin). Requires a user with `role = "admin"`.

**Seeded admin:** `$ADMIN_EMAIL` / `$ADMIN_PASSWORD` from `.env`
(default `admin@videoforge.io`).

> **Password changes:** re-running `make seed` updates the admin's **role**
> but does **not** reset the password once the account exists (the password is
> only set on first creation). To change the password, use the app's
> change-password flow, the password-reset flow, or update the hash directly
> in the database.

**Features:**

- **Overview** — metrics dashboard (users, MRR, videos, job queue).
- **Users** — search, deactivate, promote to admin.
- **Jobs** — inspect and retry failed video jobs.
- **Settings** — key/value system settings editor.
- **Audit Logs** — filterable admin action log.

### Admin paywall bypass

Admin users are **exempt** from all plan paywalls:

- No monthly video limit (`/videos/generate`).
- YouTube auto-publish is allowed on any plan.
- No watermark is burned into generated videos.
- Usage endpoints report **Unlimited** limits (`-1`), so the dashboard shows
  `/ Unlimited` instead of a plan quota.

---

## Deployment Plan (production)

VideoForge ships a production compose file (`docker-compose.production.yml`)
that runs the same stack plus **Caddy** for automatic TLS and reverse
proxying. The full runbook lives in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md);
the essentials are below.

### 1. Provision a server

A VPS/VM running **Ubuntu 22.04+** with Docker + Docker Compose v2. Create two
DNS A records pointing at the server's public IP:

| Name | Type | Value |
|---|---|---|
| `app.example.com` | A | `<server-ip>` |
| `api.example.com` | A | `<server-ip>` |

### 2. Cloud resources

- **S3 bucket** (or S3-compatible) for video storage, with
  `s3:PutObject` / `GetObject` / `DeleteObject` / `ListBucket` permissions.
- **AWS Secrets Manager** (optional) holding all secret env vars under the
  `videoforge/prod/` prefix — the API/worker auto-load them via
  `SECRETS_BACKEND=aws`. For a simpler single-server deploy, `env` works too.
- **Managed Postgres + Redis** (RDS/Supabase/Neon, Upstash/ElastiCache) are
  recommended over in-Docker instances for production.

### 3. Configure

Write a small `.env` on the server with the non-secret values:

```dotenv
PRIMARY_DOMAIN=app.example.com
API_DOMAIN=api.example.com
ACME_EMAIL=ops@example.com
POSTGRES_USER=videoforge
POSTGRES_PASSWORD=<strong>
REDIS_PASSWORD=<strong>
AWS_REGION=us-east-1
S3_BUCKET_NAME=videoforge-prod-videos
IMAGE_TAG=$(git rev-parse --short HEAD)
```

Secrets (SECRET_KEY, STRIPE_*, YOUTUBE_*, OPENAI_*, MAGIC_HOUR_API_KEY,
ADMIN_PASSWORD, …) go into Secrets Manager or the same `.env` (chmod 600) with
`SECRETS_BACKEND=env`.

### 4. Deploy

```bash
git clone <repo> /opt/videoforge && cd /opt/videoforge
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml exec api alembic upgrade head
docker compose -f docker-compose.production.yml exec api python /seed.py
```

### 5. External integrations

- **Stripe** webhook → `https://api.example.com/api/webhooks/stripe`
  (events: `checkout.session.completed`, `customer.subscription.updated`,
  `customer.subscription.deleted`, `invoice.payment_failed`).
- **YouTube OAuth** redirect URI →
  `https://api.example.com/api/oauth/youtube/callback`.

### 6. Verify & monitor

```bash
curl -fsSL https://app.example.com/health   # → {"status":"ok",...}
docker compose -f docker-compose.production.yml logs -f --tail=50
```

Confirm Caddy obtained certificates on first boot. Point an uptime probe at
`https://app.example.com/health`. Set `SENTRY_DSN` for error tracking (you must
add `sentry-sdk` to both `api/requirements.txt` and `worker/requirements.txt`
for it to take effect).

### 7. Backups & rollback

See [docs/BACKUPS.md](docs/BACKUPS.md) for the full plan. Minimum:

- Nightly `pg_dump` of Postgres (retain several days).
- Versioning/lifecycle replication on the S3 bucket to another region/account.

Every deploy is built with an `IMAGE_TAG` (git short SHA) so you can pin and
roll back images deterministically.

---

## User Guide

### Getting started

1. **Sign up** at the web app (`/register`) — you get the **Free** plan
   (4 watermarked videos/month).
2. **Log in** and open the dashboard (`/dashboard`) to see your plan, video
   usage, and recent projects.
3. Upgrade to a paid plan from **Settings → Manage subscription** (Stripe
   checkout). You'll see your new limits immediately.

### Creating a video

1. From the dashboard, click **New Project**.
2. Enter a **topic** (e.g. "Why the Roman Empire fell") — that's all the app
   needs to start.
3. Choose optional style options (tone, style, duration).
4. Submit. The job is queued and processed asynchronously:

   - **Script** — the topic is expanded into a narration script + metadata.
   - **Voiceover** — an AI narrator reads the script.
   - **Captions** — auto-generated subtitles.
   - **Visuals** — AI footage (if Magic Hour is connected) or a branded
     gradient background.
   - **Render** — captions and (on Free) a watermark are burned in.

5. Watch the video's status change (`pending → generating_script →
   generating_voiceover → assembling → completed`) on the **Videos** page.
   If something goes wrong, the status shows **failed** with an error message;
   an admin can retry failed jobs from the admin panel.

### Scheduling & publishing

- Open a **completed** video and choose a platform + publish time to create a
  schedule.
- **YouTube** videos are auto-published when the scheduled time arrives
  (requires connecting your YouTube account in **Settings**).
- **Instagram / TikTok / X** are not auto-published (no official auto-post
  APIs) — VideoForge exports a `.zip` with the video file plus caption and
  metadata text that you can upload manually.
- Free-plan users cannot auto-publish to YouTube; paid plans can. Admins are
  always allowed.

### Managing your account

- **Settings** — update your name/email, change your password, connect social
  accounts, and manage your subscription.
- **Usage** — the dashboard shows videos generated vs. your monthly limit and
  motion credits.
- **Admin** — if your role is `admin`, the **Admin** nav link opens the panel
  (metrics, users, jobs, settings, audit logs). Admin accounts skip all plan
  limits and watermarks.

---

## Notes

- **Non-YouTube platforms** (Instagram, TikTok, X): VideoForge exports a
  `.zip` with the video file + caption/metadata text. No scraping, no
  unofficial APIs.
- **Watermarks**: Free-plan videos get an overlay burned in by FFmpeg. Admin
  videos never get one.
- **Storage**: Videos live in S3 (or MinIO locally). Download URLs are
  pre-signed S3 URLs.
- **Social tokens**: YouTube OAuth tokens are encrypted at rest using Fernet
  (key derived from `SECRET_KEY`).
- **Paywall bypass**: Admin accounts are exempt from video limits, the
  watermark, and the YouTube auto-publish gate — see the Admin Panel section.
