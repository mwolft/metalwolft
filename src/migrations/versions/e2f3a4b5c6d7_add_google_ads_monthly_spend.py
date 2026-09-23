"""add manually entered Google Ads monthly spend

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
"""

from alembic import op
import sqlalchemy as sa


revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "google_ads_monthly_spend",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "month", name="uq_google_ads_spend_year_month"),
        sa.CheckConstraint("year BETWEEN 1 AND 9999", name="ck_google_ads_spend_year_valid"),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_google_ads_spend_month_valid"),
        sa.CheckConstraint("amount >= 0", name="ck_google_ads_spend_amount_nonnegative"),
    )


def downgrade():
    op.drop_table("google_ads_monthly_spend")
