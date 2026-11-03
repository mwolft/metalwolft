"""Store monthly Google Ads purchase attribution separately from orders and costs.

Revision ID: c8e4f0a2b6d9
Revises: b7d3e9f1a2c4
"""

from alembic import op
import sqlalchemy as sa


revision = "c8e4f0a2b6d9"
down_revision = "b7d3e9f1a2c4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "google_ads_purchase_monthly",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("conversions", sa.Numeric(12, 2), nullable=True),
        sa.Column("value_eur", sa.Numeric(12, 2), nullable=True),
        sa.Column("source_start", sa.Date(), nullable=True),
        sa.Column("source_end", sa.Date(), nullable=True),
        sa.Column("import_filename", sa.String(255), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=True),
        sa.Column("manual_conversions", sa.Numeric(12, 2), nullable=True),
        sa.Column("manual_value_eur", sa.Numeric(12, 2), nullable=True),
        sa.Column("manual_updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("year", "month", name="uq_ads_purchase_year_month"),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_ads_purchase_month"),
        sa.CheckConstraint("conversions >= 0 AND value_eur >= 0", name="ck_ads_purchase_values"),
        sa.CheckConstraint("manual_conversions >= 0 AND manual_value_eur >= 0", name="ck_ads_purchase_manual_values"),
    )


def downgrade():
    op.drop_table("google_ads_purchase_monthly")
