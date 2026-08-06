"""Add addon_grants table for one-time Stripe add-on purchases.

Revision ID: 0007_addon_grants
Revises: 0006_subscriptions_updated_at
Create date: 2026-08-06 00:00:00.000000

What this does:
- Creates the `addon_grants` table used to record one-time add-on purchases
  (motion credits, voice cloning packs, brand kit) credited to a user after a
  `checkout.session.completed` webhook from the /billing/checkout/addon flow.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_addon_grants"
down_revision = "0006_subscriptions_updated_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    use_uuid = dialect == "postgresql"
    uuid_type = postgresql.UUID(as_uuid=True) if use_uuid else sa.String(36)

    op.create_table(
        "addon_grants",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("product_key", sa.String(64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_addon_grants_user_id", "addon_grants", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_addon_grants_user_id", table_name="addon_grants")
    op.drop_table("addon_grants")
