"""Add missing updated_at column on subscriptions.

Revision ID: 0006_subscriptions_updated_at
Revises: 0005_deploy_additions
Create date: 2026-08-04 12:00:00.000000

What this does:
- 0001_initial created the subscriptions table without an `updated_at`
  column, but the ORM model (app/models/subscription.py) declares one with
  `onupdate=func.now()`. Every INSERT that writes a Subscription row (e.g.
  /api/auth/register provisioning a default free subscription) fails with
  `column "updated_at" of relation "subscriptions" does not exist`.

- This migration adds the column. It is nullable so existing rows survive;
  SQLAlchemy applies onupdate at the ORM level on UPDATE, so no server
  default is required.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_subscriptions_updated_at"
down_revision = "0005_deploy_additions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "updated_at")
