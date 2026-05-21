"""Phase 2 Database Expansion

Revision ID: 0002_phase2_expansion
Revises: 0001_initial
Create date: 2026-05-20 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_phase2_expansion'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    # Plans Table
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('stripe_price_id', sa.String(), nullable=True),
        sa.Column('video_limit_monthly', sa.Integer(), nullable=True),
        sa.Column('storage_limit_gb', sa.Integer(), nullable=True),
        sa.Column('motion_credits_monthly', sa.Integer(), nullable=True),
        sa.Column('features_json', sa.JSON(), nullable=True),
        sa.Column('price_cents', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plans_id', 'plans', ['id'], unique=False)
    op.create_unique_constraint('uq_plans_name', 'plans', ['name'])
    op.create_unique_constraint('uq_plans_stripe_id', 'plans', ['stripe_price_id'])

    # Usage Events Table
    op.create_table(
        'usage_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('ix_usage_events_id', 'usage_events', ['id'], unique=False)

    # Project Assets Table
    op.create_table(
        'project_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sa.String(), nullable=False),
        sa.Column('storage_key', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    )
    op.create_index('ix_project_assets_id', 'project_assets', ['id'], unique=False)

    # Prompt Templates Table
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('script_template', sa.String(), nullable=False),
        sa.Column('title_template', sa.String(), nullable=True),
        sa.Column('description_template', sa.String(), nullable=True),
        sa.Column('hashtag_template', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint('uq_prompt_templates_name', 'prompt_templates', ['name'])

    # System Settings Table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('value_type', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint('uq_system_settings_key', 'system_settings', ['key'])

    # Admin Audit Log Table
    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
    )
    op.create_index('ix_admin_audit_logs_id', 'admin_audit_logs', ['id'], unique=False)
