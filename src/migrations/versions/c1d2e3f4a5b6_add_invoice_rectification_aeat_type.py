"""add explicit AEAT classification to invoice rectifications

Revision ID: c1d2e3f4a5b6
Revises: e5f6a7b8c9d0, f1a2b3c4d5e6
Create Date: 2026-08-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c1d2e3f4a5b6"
down_revision = ("e5f6a7b8c9d0", "f1a2b3c4d5e6")
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "invoices",
        sa.Column("rectification_aeat_type", sa.String(length=2), nullable=True),
    )
    op.create_check_constraint(
        "ck_invoices_rectification_aeat_type_valid",
        "invoices",
        "rectification_aeat_type IS NULL OR rectification_aeat_type IN "
        "('R1', 'R2', 'R3', 'R4', 'R5')",
    )
    op.create_check_constraint(
        "ck_invoices_rectification_aeat_type_corrective_only",
        "invoices",
        "rectification_aeat_type IS NULL OR invoice_type = 'corrective'",
    )


def downgrade():
    op.drop_constraint(
        "ck_invoices_rectification_aeat_type_corrective_only",
        "invoices",
        type_="check",
    )
    op.drop_constraint(
        "ck_invoices_rectification_aeat_type_valid",
        "invoices",
        type_="check",
    )
    op.drop_column("invoices", "rectification_aeat_type")
