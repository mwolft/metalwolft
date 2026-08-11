"""add supplier invoice extraction proposals

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-08-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a4b5c6d7e8f9"
down_revision = "f3a4b5c6d7e8"
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
        "processing_status IN ('uploaded', 'extracting', 'extracted', 'needs_review', 'failed', 'applied')",
    )
    op.create_table(
        "supplier_invoice_extractions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_invoice_document_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("extractor_version", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="extracting"),
        sa.Column("payload_schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("extraction_payload", sa.JSON(), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('extracting', 'extracted', 'needs_review', 'failed', 'applied')",
            name="ck_supplier_invoice_extractions_status_valid",
        ),
        sa.CheckConstraint(
            "status NOT IN ('extracted', 'needs_review', 'applied') OR ("
            "extraction_payload IS NOT NULL AND payload_hash IS NOT NULL AND completed_at IS NOT NULL"
            ")",
            name="ck_supplier_invoice_extractions_completed_payload_present",
        ),
        sa.CheckConstraint(
            "status != 'failed' OR completed_at IS NOT NULL",
            name="ck_supplier_invoice_extractions_failed_completed",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_invoice_document_id"],
            ["supplier_invoice_documents.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_supplier_invoice_extractions_document_id",
        "supplier_invoice_extractions",
        ["supplier_invoice_document_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_supplier_invoice_extractions_document_id",
        table_name="supplier_invoice_extractions",
    )
    op.drop_table("supplier_invoice_extractions")
    op.drop_constraint(
        "ck_supplier_invoice_documents_processing_status_valid",
        "supplier_invoice_documents",
        type_="check",
    )
    op.create_check_constraint(
        "ck_supplier_invoice_documents_processing_status_valid",
        "supplier_invoice_documents",
        "processing_status IN ('uploaded', 'failed')",
    )
