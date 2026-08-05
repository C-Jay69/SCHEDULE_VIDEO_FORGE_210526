# VideoForge — Backups & Disaster Recovery

> Referenced from `DEPLOYMENT.md` (§8). This is the minimal, proven baseline for
> a single-server production deploy. It covers the two stateful stores that
> matter: **PostgreSQL** (relational data) and **S3** (videos/assets).

---

## 1. PostgreSQL

### Nightly logical dump (recommended)

Run on the host as a cron job (the `postgres_data` volume is in use by the
container, so we dump *through* `pg_dump` inside the container):

```bash
#!/usr/bin/env bash
# /etc/cron.daily/videoforge-backup
set -euo pipefail

BACKUP_DIR=/var/backups/videoforge
mkdir -p "$BACKUP_DIR"
KEEP=14

# Dump to a gzipped SQL file with a timestamp.
docker exec schedule_video_forge_210526-postgres-1 \
    pg_dump -U videoforge -d videoforge \
    | gzip > "$BACKUP_DIR/videoforge-$(date +%F_%H%M%S).sql.gz"

# Keep only the last $KEEP dumps.
ls -1t "$BACKUP_DIR"/videoforge-*.sql.gz | tail -n +$((KEEP + 1)) | xargs -r rm -f
```

Then sync the backup directory to an off-box destination (S3, rsync to another
host, etc.):

```bash
aws s3 sync /var/backups/videoforge s3://videoforge-backups/postgres/ --delete
```

### Restore

```bash
gunzip -c /var/backups/videoforge-<date>.sql.gz \
    | docker exec -i schedule_video_forge_210526-postgres-1 psql -U videoforge -d videoforge
```

---

## 2. S3 (videos & project assets)

Enable **versioning** on the bucket (already in the deploy guide) and add a
**cross-region replication rule** to a second bucket in a different account or
region, or a lifecycle rule that copies the bucket to a cheaper tier:

```bash
aws s3api get-bucket-versioning --bucket videoforge-prod-videos
```

- Versioning protects against accidental overwrites/deletes.
- A lifecycle rule copying old objects to Glacier/Iceberg gives point-in-time
  recovery at minimal cost:

```bash
aws s3api put-bucket-lifecycle-configuration \
    --bucket videoforge-prod-videos \
    --lifecycle-configuration file://lifecycle.json
```

Example `lifecycle.json` (transition objects > 30 days old to Glacier):

```json
{
  "Rules": [
    {
      "ID": "archive-old-videos",
      "Status": "Enabled",
      "Filter": { "Prefix": "" },
      "Transitions": [
        { "Days": 30, "StorageClass": "GLACIER" }
      ]
    }
  ]
}
```

---

## 3. Redis

Redis is a cache/queue. On restart the beat schedule re-registers and Celery
re-queues `acks_late` tasks, so a cold Redis cache is **not** a data-loss event
for us. No separate backup is required; just don't delete the `redis_data`
volume with `docker compose down -v`.

---

## 4. Scheduled, verified restore drill

- At least monthly, restore a `pg_dump` into a throwaway database and confirm
  the admin user + a sample row are present.
- List the S3 bucket and confirm objects older than 30 days transitioned to
  the archive class.

---

## TL;DR

| Store     | Backup                              | Frequency | Retention |
|-----------|-------------------------------------|-----------|-----------|
| Postgres  | `pg_dump` → gzip → sync to S3       | daily     | 14 d local |
| S3        | versioning + lifecycle to Glacier   | continuous| 30 d / archive |
| Redis     | none (rebuildable cache/queue)      | —         | —         |
