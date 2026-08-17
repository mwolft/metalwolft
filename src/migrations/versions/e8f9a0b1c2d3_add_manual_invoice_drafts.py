"""add manual invoice drafts

Revision ID: e8f9a0b1c2d3
Revises: a1b2c3d4e5f6
Create Date: 2026-08-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e8f9a0b1c2d3"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "manual_invoice_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=True),
        sa.Column("client_tax_id", sa.String(length=50), nullable=True),
        sa.Column("client_address", sa.String(length=255), nullable=True),
        sa.Column("client_postal_code", sa.String(length=20), nullable=True),
        sa.Column("client_city", sa.String(length=100), nullable=True),
        sa.Column("client_province", sa.String(length=100), nullable=True),
        sa.Column("client_country_code", sa.String(length=2), server_default="ES", nullable=False),
        sa.Column("client_email", sa.String(length=255), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("operation_date", sa.Date(), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("issuance_key", sa.String(length=36), nullable=False),
        sa.Column("issued_invoice_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("issued_by", sa.String(length=255), nullable=True),
        sa.CheckConstraint("status IN ('draft', 'issued', 'cancelled')", name="ck_manual_invoice_drafts_status_valid"),
        sa.CheckConstraint("currency = 'EUR'", name="ck_manual_invoice_drafts_currency_eur"),
        sa.CheckConstraint("client_country_code = 'ES'", name="ck_manual_invoice_drafts_client_country_es"),
        sa.ForeignKeyConstraint(["issued_invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issuance_key"),
        sa.UniqueConstraint("issued_invoice_id"),
    )
    op.create_table(
        "manual_invoice_draft_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("manual_invoice_draft_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), server_default="1", nullable=False),
        sa.Column("concept", sa.String(length=500), nullable=True),
        sa.Column("tax_base", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("tax_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.CheckConstraint("tax_base > 0", name="ck_manual_invoice_draft_lines_tax_base_positive"),
        sa.CheckConstraint("tax_rate >= 0", name="ck_manual_invoice_draft_lines_tax_rate_nonnegative"),
        sa.ForeignKeyConstraint(["manual_invoice_draft_id"], ["manual_invoice_drafts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("manual_invoice_draft_id", "position", name="uq_manual_invoice_draft_lines_position"),
    )


def downgrade():
    op.drop_table("manual_invoice_draft_lines")
    op.drop_table("manual_invoice_drafts")
