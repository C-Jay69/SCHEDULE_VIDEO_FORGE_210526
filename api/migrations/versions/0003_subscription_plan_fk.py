"""Subscription plan -> Plan FK migration

Revision ID: 0003_subscription_plan_fk
Revises: 0002_phase2_expansion
Create date: 2026-08-03 10:00:00.000000

What this does:
- Adds a nullable plan_id column on subscriptions pointing at plans.id.
- Backfills it from the legacy PlanType enum + a small mapping:
    enum 'free'    -> Plan row named 'free'
    enum 'creator' -> Plan row named 'scheduler' (the actual paid tier)
    enum 'pro'     -> Plan row named 'intense'  (the actual pro tier)
- If a backfill target is missing from the plans table, we silently default
  to whatever Plan row is named 'free'. This keeps the migration idempotent
  even when seed.py hasn't run yet.
- Drops the legacy `plan` enum column + its Postgres ENUM type.
- Adds a NOT NULL constraint on plan_id once the backfill is done.

Why two stages: a fresh database (no rows) is fine; a production database
with existing rows would crash if we tried NOT NULL before backfilling.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_subscription_plan_fk"
down_revision = "0002_phase2_expansion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add plan_id column (nullable first so existing rows survive)
    op.add_column(
        "subscriptions",
        sa.Column("plan_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_subscriptions_plan_id",
        "subscriptions",
        "plans",
        ["plan_id"],
        ["id"],
    )
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])

    # 2. Backfill plan_id from legacy enum using a subquery on plans.
    bind = op.get_bind()
    # Map legacy enum value -> plan.name
    mapping = {
        "free": "free",
        "creator": "scheduler",
        "pro": "intense",
    }

    # Make sure all four plans exist before mapping — if seed hasn't run,
    # insert missing plan rows so the FK constraint can succeed.
    existing = {row[0] for row in bind.execute(sa.text("SELECT name FROM plans")).fetchall()}
    plan_defaults = [
        ("free", 4, 1, 0, "[]", 0),
        ("scheduler", 13, 10, 27, '["no_watermark","auto_publish","hd"]', 1500),
        ("committed", 30, 50, 62, '["no_watermark","auto_publish","hd","voice_cloning"]', 3000),
        ("intense", 62, 200, 124, '["no_watermark","auto_publish","hd","voice_cloning","priority_queue"]', 5500),
    ]
    for name, vid_lim, stor, creds, feats, price in plan_defaults:
        if name not in existing:
            bind.execute(
                sa.text(
                    "INSERT INTO plans (name, video_limit_monthly, storage_limit_gb, "
                    "motion_credits_monthly, features_json, price_cents, is_active) "
                    "VALUES (:n, :vl, :st, :mc, :f, :p, true)"
                ),
                {"n": name, "vl": vid_lim, "st": stor, "mc": creds, "f": feats, "p": price},
            )

    # 3. For each legacy value, point plan_id at the matching Plan row.
    for legacy_name, target_plan_name in mapping.items():
        bind.execute(
            sa.text(
                "UPDATE subscriptions AS s SET plan_id = p.id "
                "FROM plans AS p "
                "WHERE s.plan::text = :legacy AND p.name = :target AND s.plan_id IS NULL"
            ),
            {"legacy": legacy_name, "target": target_plan_name},
        )

    # 4. Anything still NULL (no enum set, plans existed but no row matched)
    # falls back to the 'free' plan so the NOT NULL constraint can be applied.
    bind.execute(
        sa.text(
            "UPDATE subscriptions AS s SET plan_id = p.id FROM plans AS p WHERE p.name = 'free' AND s.plan_id IS NULL"
        )
    )

    # 5. NOW make plan_id mandatory.
    op.alter_column("subscriptions", "plan_id", nullable=False)

    # 6. Drop the legacy column + enum type.
    op.drop_column("subscriptions", "plan")
    op.execute("DROP TYPE IF EXISTS plantype")


def downgrade() -> None:
    # 1. Re-add the enum column (nullable so we don't lose data).
    plantype = sa.Enum("free", "creator", "pro", name="plantype")
    plantype.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "subscriptions",
        sa.Column("plan", plantype, nullable=True),
    )

    # 2. Backfill enum from plan_id by joining plans -> name.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE subscriptions AS s SET plan = 'free'::plantype "
            "FROM plans AS p WHERE p.id = s.plan_id AND p.name = 'free'"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE subscriptions AS s SET plan = 'creator'::plantype "
            "FROM plans AS p WHERE p.id = s.plan_id AND p.name IN ('scheduler', 'committed')"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE subscriptions AS s SET plan = 'pro'::plantype "
            "FROM plans AS p WHERE p.id = s.plan_id AND p.name = 'intense'"
        )
    )

    # 3. Make it NOT NULL with a safe default.
    op.alter_column("subscriptions", "plan", nullable=False, server_default="free")

    # 4. Drop the FK + column.
    op.drop_constraint("fk_subscriptions_plan_id", "subscriptions", type_="foreignkey")
    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_column("subscriptions", "plan_id")
