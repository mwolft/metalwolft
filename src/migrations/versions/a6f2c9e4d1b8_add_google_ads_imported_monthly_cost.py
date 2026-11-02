"""Store source-backed monthly Google Ads CSV costs separately from manual spend.

Revision ID: a6f2c9e4d1b8
Revises: b4c5d6e7f8a9
"""

from alembic import op
import sqlalchemy as sa


revision = "a6f2c9e4d1b8"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "google_ads_imported_monthly_cost",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("source_start", sa.Date(), nullable=False),
        sa.Column("source_end", sa.Date(), nullable=False),
        sa.Column("source_days", sa.Integer(), nullable=False),
        sa.Column("cost_eur", sa.Numeric(12, 2), nullable=False),
        sa.Column("cost_product_eur", sa.Numeric(12, 2), nullable=False),
        sa.Column("cost_without_product_eur", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(100), nullable=False),
        sa.Column("import_filename", sa.String(255), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("year", "month", name="uq_ads_import_year_month"),
        sa.CheckConstraint("year BETWEEN 1900 AND 9998", name="ck_ads_import_year"),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_ads_import_month"),
        sa.CheckConstraint("source_days BETWEEN 1 AND 31", name="ck_ads_import_days"),
        sa.CheckConstraint("cost_eur >= 0 AND cost_product_eur >= 0 AND cost_without_product_eur >= 0",
                           name="ck_ads_import_cost_nonnegative"),
        sa.CheckConstraint("ROUND(cost_eur - cost_product_eur - cost_without_product_eur, 2) = 0",
                           name="ck_ads_import_cost_components"),
    )


def downgrade():
    op.drop_table("google_ads_imported_monthly_cost")
