"""Add sessions, platform_tokens, webhook_events, billing_events.

Revision ID: 0005_deploy_additions
Revises: 0004_settings_json_portable
Create date: 2026-08-04 12:00:00.000000

Adds the four tables that the spec's DATABASE REQUIREMENTS section lists
but the initial schema never created:

  sessions        — server-side session tracking (JWT audit trail)
  platform_tokens — split access/refresh tokens out of social_accounts
                    (kept additive so existing rows still work)
  webhook_events  — persisted webhook inbox for Stripe/YouTube delivery
  billing_events  — billing ledger (invoices, failures, plan changes)

All new tables use portable types (JSON, not JSONB) so the schema works on
both Postgres and SQLite for tests.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "0005_deploy_additions"
down_revision = "0004_settings_json_portable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    use_uuid = dialect == "postgresql"
    uuid_type = UUID(as_uuid=True) if use_uuid else sa.String(36)

    op.create_table(
        "sessions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.create_table(
        "platform_tokens",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "social_account_id", uuid_type, sa.ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(50), nullable=True),
        sa.Column("scope", sa.String(512), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_platform_tokens_social_account_id", "platform_tokens", ["social_account_id"])

    op.create_table(
        "webhook_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=True),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_webhook_events_event_id", "webhook_events", ["event_id"])
    op.create_index("ix_webhook_events_processed", "webhook_events", ["processed"])

    op.create_table(
        "billing_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("stripe_event_id", sa.String(255), nullable=True),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_billing_events_stripe_event_id", "billing_events", ["stripe_event_id"])
    op.create_index("ix_billing_events_user_id", "billing_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("billing_events")
    op.drop_table("webhook_events")
    op.drop_table("platform_tokens")
    op.drop_table("sessions")
