"""add supplier document deletion retry states

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-08-12 00:00:00.000000
"""

from alembic import op


revision = "c6d7e8f9a0b1"
down_revision = "b5c6d7e8f9a0"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "ck_supplier_invoice_documents_processing_status_valid",
        "supplier_invoice_documents",
        type_="check",
    )
    op.create_check_constraint(
        "ck_supplier_invoice_documents_processing_status_valid",
        "supplier_invoice_documents",
        "processing_status IN ('uploaded', 'extracting', 'extracted', 'needs_review', 'failed', "
        "'applied', 'deleting', 'delete_failed')",
    )


def downgrade():
    op.drop_constraint(
        "ck_supplier_invoice_documents_processing_status_valid",
        "supplier_invoice_documents",
        type_="check",
    )
    op.create_check_constraint(
        "ck_supplier_invoice_documents_processing_status_valid",
        "supplier_invoice_documents",
        "processing_status IN ('uploaded', 'extracting', 'extracted', 'needs_review', 'failed', 'applied')",
    )
