"""Make Project.settings_json portable (JSONB -> JSON).

Revision ID: 0004_settings_json_portable
Revises: 0003_subscription_plan_fk
Create date: 2026-08-03 11:00:00.000000

Why: the original column used postgresql.JSONB, which is only compileable
on Postgres. This broke the test suite (and any contributor running locally
against SQLite, which is the default in conftest). The application code
only stores a flat dict — JSONB features (indexing on jsonb_path_ops,
containment operators) aren't used anywhere — so the portable JSON type
is a perfectly fine drop-in.

Postgres still has a `JSON` type that stores as text and supports the same
operators as JSONB (with slightly weaker index performance, which we
don't use).

The migration only does work when the underlying column is JSONB. SQLite
runs no-op.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_settings_json_portable"
down_revision = "0003_subscription_plan_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # ALTER COLUMN ... TYPE json USING settings_json::text::json is the
        # standard JSONB -> JSON conversion. The USING clause is required
        # because Postgres won't auto-coerce between the two.
        op.execute("ALTER TABLE projects ALTER COLUMN settings_json TYPE json USING settings_json::text::json")
    # SQLite / MySQL / etc.: the model change already reflects the new type.
    # Production was always Postgres, so this matches.

    # Keep the SQLAlchemy metadata aware. We use batch_alter_table only when
    # we actually need to alter the column type — skipped here because the
    # ALTER did the work directly.


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE projects ALTER COLUMN settings_json TYPE jsonb USING settings_json::text::jsonb")
