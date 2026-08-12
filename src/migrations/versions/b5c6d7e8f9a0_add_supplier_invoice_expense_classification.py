"""add supplier invoice expense classification snapshot v2 fields

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-08-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b5c6d7e8f9a0"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_invoices",
        sa.Column("aeat_expense_concept_code", sa.String(length=3), nullable=True),
    )
    op.add_column(
        "supplier_invoices",
        sa.Column("expense_deductible_amount", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.drop_constraint(
        "ck_supplier_invoices_registered_snapshot_complete",
        "supplier_invoices",
        type_="check",
    )
    op.create_check_constraint(
        "ck_supplier_invoices_registered_snapshot_complete",
        "supplier_invoices",
        "status != 'registered' OR ("
        "reception_number IS NOT NULL AND registered_at IS NOT NULL AND "
        "fiscal_snapshot IS NOT NULL AND snapshot_schema_version IN (1, 2) AND "
        "snapshot_hash IS NOT NULL"
        ")",
    )
    op.create_check_constraint(
        "ck_supplier_invoices_aeat_expense_concept_code_valid",
        "supplier_invoices",
        "aeat_expense_concept_code IS NULL OR "
        "aeat_expense_concept_code IN ('G01', 'G03', 'G22', 'G24')",
    )
    op.create_check_constraint(
        "ck_supplier_invoices_expense_deductible_amount_nonnegative",
        "supplier_invoices",
        "expense_deductible_amount IS NULL OR expense_deductible_amount >= 0",
    )


def downgrade():
    op.drop_constraint(
        "ck_supplier_invoices_expense_deductible_amount_nonnegative",
        "supplier_invoices",
        type_="check",
    )
    op.drop_constraint(
        "ck_supplier_invoices_aeat_expense_concept_code_valid",
        "supplier_invoices",
        type_="check",
    )
    op.drop_constraint(
        "ck_supplier_invoices_registered_snapshot_complete",
        "supplier_invoices",
        type_="check",
    )
    op.create_check_constraint(
        "ck_supplier_invoices_registered_snapshot_complete",
        "supplier_invoices",
        "status != 'registered' OR ("
        "reception_number IS NOT NULL AND registered_at IS NOT NULL AND "
        "fiscal_snapshot IS NOT NULL AND snapshot_schema_version = 1 AND "
        "snapshot_hash IS NOT NULL"
        ")",
    )
    op.drop_column("supplier_invoices", "expense_deductible_amount")
    op.drop_column("supplier_invoices", "aeat_expense_concept_code")
