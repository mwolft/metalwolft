"""add private supplier invoice documents

Revision ID: f3a4b5c6d7e8
Revises: d2e3f4a5b6c7
Create Date: 2026-08-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f3a4b5c6d7e8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supplier_invoice_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_invoice_id", sa.Integer(), nullable=True),
        sa.Column("storage_provider", sa.String(length=20), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("processing_status", sa.String(length=30), server_default="uploaded", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "storage_provider IN ('r2')",
            name="ck_supplier_invoice_documents_storage_provider_valid",
        ),
        sa.CheckConstraint(
            "file_size > 0",
            name="ck_supplier_invoice_documents_file_size_positive",
        ),
        sa.CheckConstraint(
            "processing_status IN ('uploaded', 'failed')",
            name="ck_supplier_invoice_documents_processing_status_valid",
        ),
        sa.CheckConstraint(
            "sha256 <> ''",
            name="ck_supplier_invoice_documents_sha256_present",
        ),
        sa.CheckConstraint(
            "storage_key <> ''",
            name="ck_supplier_invoice_documents_storage_key_present",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_invoice_id"],
            ["supplier_invoices.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(
        "ix_supplier_invoice_documents_sha256",
        "supplier_invoice_documents",
        ["sha256"],
        unique=False,
    )
    op.create_index(
        "ix_supplier_invoice_documents_supplier_invoice_id",
        "supplier_invoice_documents",
        ["supplier_invoice_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_supplier_invoice_documents_supplier_invoice_id",
        table_name="supplier_invoice_documents",
    )
    op.drop_index(
        "ix_supplier_invoice_documents_sha256",
        table_name="supplier_invoice_documents",
    )
    op.drop_table("supplier_invoice_documents")
