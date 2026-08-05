# VideoForge — Production Deployment Guide

This guide walks through deploying VideoForge to a VPS / cloud VM. For the
quickest path, scroll to **TL;DR** at the bottom.

---

## 0. Prerequisites

- A server (VPS, EC2, bare metal) running Ubuntu 22.04+ with Docker + Docker
  Compose v2 installed.
- A domain name with DNS pointing at the server's public IP.
- AWS account (for S3 + Secrets Manager) OR equivalent.

## 1. DNS

Create two A records (or one A + CNAME):

| Name                | Type | Value             |
|---------------------|------|-------------------|
| `app.example.com`   | A    | `<server-ip>`     |
| `api.example.com`   | A    | `<server-ip>`     |

(Tweak the domain to your own; the Caddyfile uses `PRIMARY_DOMAIN` /
`API_DOMAIN` so you can keep them as is.)

## 2. Create AWS resources

### S3 bucket

```bash
aws s3api create-bucket \
    --bucket videoforge-prod-videos \
    --region us-east-1 \
    --create-bucket-configuration LocationConstraint=us-east-1

aws s3api put-bucket-versioning \
    --bucket videoforge-prod-videos \
    --versioning-configuration Status=Enabled
```

The IAM policy needs `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`,
`s3:ListBucket` on this bucket.

### Secrets Manager

```bash
# These are the keys our secrets loader knows about
for key in SECRET_KEY DATABASE_URL REDIS_URL \
           STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET \
           STRIPE_PUBLISHABLE_KEY NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY \
           STRIPE_FREE_PRICE_ID STRIPE_SCHEDULER_PRICE_ID \
           STRIPE_COMMITTED_PRICE_ID STRIPE_INTENSE_PRICE_ID \
           YOUTUBE_CLIENT_ID YOUTUBE_CLIENT_SECRET \
           OPENAI_API_KEY ADMIN_PASSWORD; do
    aws secretsmanager create-secret \
        --name "videoforge/prod/${key}" \
        --secret-string "${!key}" \
        --region us-east-1
done
```

The EC2/ECS/EKS instance needs an IAM role with `secretsmanager:GetSecretValue`
on `arn:aws:secretsmanager:*:*:secret:videoforge/prod/*`.

### IAM role for the host

The simplest path is to attach the role to the EC2 instance; Docker containers
inherit the metadata service credentials. Compose sets `AWS_REGION` so
boto3 picks the right endpoint.

## 3. Postgres + Redis

The compose file expects `POSTGRES_USER`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`
in env. Set strong values; do NOT reuse the dev defaults.

In production, consider a managed Postgres (RDS, Supabase, Neon) and Redis
(Upstash, ElastiCache) instead of running them in Docker. If you swap those
out, set `DATABASE_URL` and `REDIS_URL` accordingly and remove the postgres
+ redis services from the compose file.

## 4. Stripe webhook

Add a webhook endpoint in the Stripe dashboard pointing to:

```
https://api.example.com/api/webhooks/stripe
```

Listen for: `checkout.session.completed`, `customer.subscription.updated`,
`customer.subscription.deleted`, `invoice.payment_failed`.

Copy the signing secret to AWS Secrets Manager as
`videoforge/prod/STRIPE_WEBHOOK_SECRET`.

## 5. YouTube OAuth

In Google Cloud Console:

1. Create a project.
2. Enable YouTube Data API v3.
3. OAuth consent screen — add scopes for YouTube uploads.
4. Create OAuth 2.0 credentials → Web application.
5. Add `https://api.example.com/api/oauth/youtube/callback` to authorized
   redirect URIs.

Put the client ID + secret into AWS Secrets Manager.

## 6. Deploy

```bash
git clone <repo> /opt/videoforge
cd /opt/videoforge

# Provision a .env on the server (only needed for the few non-secret values)
cat > .env <<EOF
PRIMARY_DOMAIN=app.example.com
API_DOMAIN=api.example.com
ACME_EMAIL=ops@example.com
POSTGRES_USER=videoforge
POSTGRES_PASSWORD=<from your password manager>
REDIS_PASSWORD=<from your password manager>
AWS_REGION=us-east-1
S3_BUCKET_NAME=videoforge-prod-videos
SENTRY_DSN=
IMAGE_TAG=$(git rev-parse --short HEAD)
EOF
chmod 600 .env

docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml exec api alembic upgrade head
docker compose -f docker-compose.production.yml exec api python /seed.py
```

## 7. Verify

```bash
curl -fsSL https://app.example.com/health
# → {"status":"ok","service":"videoforge-api"}

# Watch logs
docker compose -f docker-compose.production.yml logs -f --tail=50
```

Check Caddy obtained a cert (look for `obtained certificate` in the caddy
container logs on first boot).

## 8. Backups

See `docs/BACKUPS.md` (added in Item 11). At minimum: nightly `pg_dump`
of Postgres + lifecycle-rule replication of the S3 bucket to a separate
account or region.

## 9. Monitoring

The compose file passes `SENTRY_DSN` to both api and worker if you set it. To
make it effective, install the SDK inside the images (add `sentry-sdk` to
`api/requirements.txt` and `worker/requirements.txt`) — or skip Sentry entirely;
the API logs structured requests via middleware and both containers log to
stdout (visible with `docker compose logs`). For uptime monitoring, point a
probe at `https://app.example.com/health`.

---

## TL;DR

1. DNS → server IP.
2. S3 bucket + AWS Secrets Manager populated.
3. Clone repo on server.
4. Write a 9-line `.env` with non-secret values.
5. `docker compose -f docker-compose.production.yml up -d --build`.
6. Run migrations + seed.
7. Verify `https://app.example.com/health` returns 200.

## Choosing a secrets backend

| Backend   | When to use                                                            |
|-----------|------------------------------------------------------------------------|
| `env`     | Local dev, single-server deploys, k8s with `envFrom: secretKeyRef`     |
| `file`    | Docker swarm secrets, k8s with `volumeMounts: secretRef`, Hashicorp    |
|           | Vault agent                                                           |
| `aws`     | AWS-hosted prod with IAM instance roles                                |

Set via `SECRETS_BACKEND=aws` (or `file`) in the environment. Defaults to
`env` so existing setups keep working.