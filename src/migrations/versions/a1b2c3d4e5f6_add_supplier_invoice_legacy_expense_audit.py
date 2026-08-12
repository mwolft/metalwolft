"""add audited legacy expense completion fields to supplier invoices

Revision ID: a1b2c3d4e5f6
Revises: d7e8f9a0b1c2
Create Date: 2026-08-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("supplier_invoices", sa.Column("legacy_expense_classified_at", sa.DateTime(), nullable=True))
    op.add_column("supplier_invoices", sa.Column("legacy_expense_classified_by", sa.String(length=255), nullable=True))
    op.add_column("supplier_invoices", sa.Column("legacy_expense_received_at", sa.Date(), nullable=True))
    op.create_check_constraint(
        "ck_supplier_invoices_legacy_expense_audit",
        "supplier_invoices",
        "(legacy_expense_classified_at IS NULL AND legacy_expense_classified_by IS NULL) OR "
        "(legacy_expense_classified_at IS NOT NULL AND legacy_expense_classified_by IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint(
        "ck_supplier_invoices_legacy_expense_audit",
        "supplier_invoices",
        type_="check",
    )
    op.drop_column("supplier_invoices", "legacy_expense_received_at")
    op.drop_column("supplier_invoices", "legacy_expense_classified_by")
    op.drop_column("supplier_invoices", "legacy_expense_classified_at")
