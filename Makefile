.PHONY: setup up down restart logs migrate seed model test lint clean

# ── Setup ──────────────────────────────────────────────────────────────────────
setup:
	@echo "→ Copying env..."
	cp -n .env.example .env || true
	@echo "→ Done. Edit .env then run: make up"

# ── Docker ─────────────────────────────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

restart-api:
	docker compose restart api

restart-worker:
	docker compose restart worker

restart-web:
	docker compose restart web

# ── Logs ───────────────────────────────────────────────────────────────────────
logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

logs-web:
	docker compose logs -f web

# ── Database ───────────────────────────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

migrate-down:
	docker compose exec api alembic downgrade -1

migrate-history:
	docker compose exec api alembic history

# Auto-generate a migration from model changes
# Usage: make model name="add_user_avatar"
model:
	@[ "$(name)" ] || ( echo "Usage: make model name=<migration_name>"; exit 1 )
	docker compose exec api alembic revision --autogenerate -m "$(name)"

# ── Seed ───────────────────────────────────────────────────────────────────────
seed:
	docker compose exec api python /app/../seed.py

# ── Testing ────────────────────────────────────────────────────────────────────
test:
	docker compose exec api pytest -v

test-watch:
	docker compose exec api pytest -v --watch

# ── Linting ────────────────────────────────────────────────────────────────────
lint:
	docker compose exec api ruff check .
	docker compose exec web npm run lint

fmt:
	docker compose exec api ruff format .

# ── Clean ──────────────────────────────────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# ── Dev helpers ────────────────────────────────────────────────────────────────
psql:
	docker compose exec db psql -U postgres -d videoforge

redis-cli:
	docker compose exec redis redis-cli

shell-api:
	docker compose exec api bash

shell-worker:
	docker compose exec worker bash

# ── Status ─────────────────────────────────────────────────────────────────────
status:
	docker compose ps

flower:
	@echo "Flower (Celery monitor) running at http://localhost:5555"
	docker compose exec worker celery -A celery_app flower --port=5555
