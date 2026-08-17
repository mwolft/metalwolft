"""add manual invoice corrective credits

Revision ID: f0a1b2c3d4e5
Revises: e8f9a0b1c2d3
Create Date: 2026-08-17 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f0a1b2c3d4e5"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("manual_invoice_drafts", sa.Column("document_nature", sa.String(length=20), server_default="ordinary", nullable=False))
    op.add_column("manual_invoice_drafts", sa.Column("original_invoice_id", sa.Integer(), nullable=True))
    op.add_column("manual_invoice_drafts", sa.Column("external_original_invoice_number", sa.String(length=50), nullable=True))
    op.add_column("manual_invoice_drafts", sa.Column("external_original_issue_date", sa.Date(), nullable=True))
    op.add_column("manual_invoice_drafts", sa.Column("rectification_reason", sa.String(length=50), nullable=True))
    op.add_column("manual_invoice_drafts", sa.Column("rectification_aeat_type", sa.String(length=2), nullable=True))
    op.create_foreign_key(
        "fk_manual_invoice_drafts_original_invoice_id",
        "manual_invoice_drafts",
        "invoices",
        ["original_invoice_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_manual_invoice_drafts_document_nature_valid",
        "manual_invoice_drafts",
        "document_nature IN ('ordinary', 'corrective')",
    )
    op.create_check_constraint(
        "ck_manual_invoice_drafts_rectification_aeat_valid",
        "manual_invoice_drafts",
        "rectification_aeat_type IS NULL OR rectification_aeat_type IN ('R1', 'R4')",
    )

    op.drop_constraint("ck_manual_invoice_draft_lines_tax_base_positive", "manual_invoice_draft_lines", type_="check")
    op.create_check_constraint(
        "ck_manual_invoice_draft_lines_tax_base_nonzero",
        "manual_invoice_draft_lines",
        "tax_base IS NULL OR tax_base <> 0",
    )

    op.add_column("invoices", sa.Column("external_original_invoice_number", sa.String(length=50), nullable=True))
    op.add_column("invoices", sa.Column("external_original_issue_date", sa.Date(), nullable=True))
    op.drop_constraint("ck_invoices_rectification_consistency", "invoices", type_="check")
    op.create_check_constraint(
        "ck_invoices_rectification_consistency",
        "invoices",
        "(invoice_type IS NULL AND original_invoice_id IS NULL AND external_original_invoice_number IS NULL AND external_original_issue_date IS NULL AND rectification_type IS NULL AND rectification_reason IS NULL) OR "
        "(invoice_type = 'ordinary' AND original_invoice_id IS NULL AND external_original_invoice_number IS NULL AND external_original_issue_date IS NULL AND rectification_type IS NULL AND rectification_reason IS NULL) OR "
        "(invoice_type = 'corrective' AND rectification_type IS NOT NULL AND rectification_reason IS NOT NULL AND ((original_invoice_id IS NOT NULL AND original_invoice_id != id AND external_original_invoice_number IS NULL AND external_original_issue_date IS NULL) OR (original_invoice_id IS NULL AND external_original_invoice_number IS NOT NULL AND external_original_invoice_number <> '' AND external_original_issue_date IS NOT NULL)))",
    )


def downgrade():
    op.drop_constraint("ck_invoices_rectification_consistency", "invoices", type_="check")
    op.create_check_constraint(
        "ck_invoices_rectification_consistency",
        "invoices",
        "(invoice_type IS NULL AND original_invoice_id IS NULL AND rectification_type IS NULL AND rectification_reason IS NULL) OR "
        "(invoice_type = 'ordinary' AND original_invoice_id IS NULL AND rectification_type IS NULL AND rectification_reason IS NULL) OR "
        "(invoice_type = 'corrective' AND original_invoice_id IS NOT NULL AND original_invoice_id != id AND rectification_type IS NOT NULL AND rectification_reason IS NOT NULL)",
    )
    op.drop_column("invoices", "external_original_issue_date")
    op.drop_column("invoices", "external_original_invoice_number")

    op.drop_constraint("ck_manual_invoice_draft_lines_tax_base_nonzero", "manual_invoice_draft_lines", type_="check")
    op.create_check_constraint(
        "ck_manual_invoice_draft_lines_tax_base_positive",
        "manual_invoice_draft_lines",
        "tax_base > 0",
    )

    op.drop_constraint("ck_manual_invoice_drafts_rectification_aeat_valid", "manual_invoice_drafts", type_="check")
    op.drop_constraint("ck_manual_invoice_drafts_document_nature_valid", "manual_invoice_drafts", type_="check")
    op.drop_constraint("fk_manual_invoice_drafts_original_invoice_id", "manual_invoice_drafts", type_="foreignkey")
    op.drop_column("manual_invoice_drafts", "rectification_aeat_type")
    op.drop_column("manual_invoice_drafts", "rectification_reason")
    op.drop_column("manual_invoice_drafts", "external_original_issue_date")
    op.drop_column("manual_invoice_drafts", "external_original_invoice_number")
    op.drop_column("manual_invoice_drafts", "original_invoice_id")
    op.drop_column("manual_invoice_drafts", "document_nature")
