"""Add audit history for manual Google Ads monthly costs.

Revision ID: b7d3e9f1a2c4
Revises: a6f2c9e4d1b8
"""

from alembic import op
import sqlalchemy as sa


revision = "b7d3e9f1a2c4"
down_revision = "a6f2c9e4d1b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "google_ads_monthly_spend_change",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("old_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("new_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("google_ads_monthly_spend_change")
