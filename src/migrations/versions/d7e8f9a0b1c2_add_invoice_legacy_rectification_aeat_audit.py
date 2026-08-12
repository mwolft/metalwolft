"""add audit fields for legacy rectification AEAT classification

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-08-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d7e8f9a0b1c2"
down_revision = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "invoices",
        sa.Column("rectification_aeat_classified_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column("rectification_aeat_classified_by", sa.String(length=255), nullable=True),
    )
    op.create_check_constraint(
        "ck_invoices_rectification_aeat_classified_at_corrective_only",
        "invoices",
        "rectification_aeat_classified_at IS NULL OR invoice_type = 'corrective'",
    )
    op.create_check_constraint(
        "ck_invoices_rectification_aeat_classified_by_corrective_only",
        "invoices",
        "rectification_aeat_classified_by IS NULL OR invoice_type = 'corrective'",
    )
    op.create_check_constraint(
        "ck_invoices_rectification_aeat_classification_audit_complete",
        "invoices",
        "(rectification_aeat_classified_at IS NULL AND rectification_aeat_classified_by IS NULL) OR "
        "(rectification_aeat_classified_at IS NOT NULL AND rectification_aeat_classified_by IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint(
        "ck_invoices_rectification_aeat_classification_audit_complete",
        "invoices",
        type_="check",
    )
    op.drop_constraint(
        "ck_invoices_rectification_aeat_classified_by_corrective_only",
        "invoices",
        type_="check",
    )
    op.drop_constraint(
        "ck_invoices_rectification_aeat_classified_at_corrective_only",
        "invoices",
        type_="check",
    )
    op.drop_column("invoices", "rectification_aeat_classified_by")
    op.drop_column("invoices", "rectification_aeat_classified_at")
