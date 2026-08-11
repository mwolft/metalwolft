"""add supplier invoices and tax breakdown persistence

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supplier_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_legal_name", sa.String(length=255), nullable=True),
        sa.Column("supplier_tax_id", sa.String(length=50), nullable=True),
        sa.Column("supplier_country_code", sa.String(length=2), server_default="ES", nullable=False),
        sa.Column("supplier_tax_id_type", sa.String(length=20), server_default="NIF", nullable=False),
        sa.Column("supplier_invoice_number", sa.String(length=100), nullable=True),
        sa.Column("reception_number", sa.Integer(), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("operation_date", sa.Date(), nullable=True),
        sa.Column("received_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
        sa.Column("registered_by", sa.String(length=255), nullable=True),
        sa.Column("concept", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("fiscal_invoice_type", sa.String(length=10), server_default="F1", nullable=False),
        sa.Column("tax_treatment", sa.String(length=40), server_default="domestic_standard", nullable=False),
        sa.Column("special_regime_key", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="draft", nullable=False),
        sa.Column("source", sa.String(length=30), server_default="manual", nullable=False),
        sa.Column("fiscal_snapshot", sa.JSON(), nullable=True),
        sa.Column("snapshot_schema_version", sa.Integer(), nullable=True),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'needs_review', 'registered', 'cancelled')",
            name="ck_supplier_invoices_status_valid",
        ),
        sa.CheckConstraint("currency = 'EUR'", name="ck_supplier_invoices_currency_eur"),
        sa.CheckConstraint("supplier_country_code = 'ES'", name="ck_supplier_invoices_country_es"),
        sa.CheckConstraint("supplier_tax_id_type = 'NIF'", name="ck_supplier_invoices_tax_id_type_nif"),
        sa.CheckConstraint("fiscal_invoice_type = 'F1'", name="ck_supplier_invoices_fiscal_type_f1"),
        sa.CheckConstraint(
            "tax_treatment = 'domestic_standard'",
            name="ck_supplier_invoices_tax_treatment_domestic_standard",
        ),
        sa.CheckConstraint(
            "reception_number IS NULL OR reception_number >= 1",
            name="ck_supplier_invoices_reception_number_positive",
        ),
        sa.CheckConstraint(
            "status != 'registered' OR ("
            "reception_number IS NOT NULL AND registered_at IS NOT NULL AND "
            "fiscal_snapshot IS NOT NULL AND snapshot_schema_version = 1 AND "
            "snapshot_hash IS NOT NULL"
            ")",
            name="ck_supplier_invoices_registered_snapshot_complete",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reception_number"),
    )
    op.create_index(
        "ix_supplier_invoices_supplier_tax_id_invoice_number",
        "supplier_invoices",
        ["supplier_tax_id", "supplier_invoice_number"],
        unique=False,
    )

    op.create_table(
        "supplier_invoice_tax_breakdowns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_invoice_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("tax_base", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("deductible_tax_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint("position >= 1", name="ck_supplier_invoice_tax_breakdowns_position_positive"),
        sa.CheckConstraint("tax_base >= 0", name="ck_supplier_invoice_tax_breakdowns_tax_base_nonnegative"),
        sa.CheckConstraint("tax_rate >= 0", name="ck_supplier_invoice_tax_breakdowns_tax_rate_nonnegative"),
        sa.CheckConstraint("tax_amount >= 0", name="ck_supplier_invoice_tax_breakdowns_tax_amount_nonnegative"),
        sa.CheckConstraint(
            "deductible_tax_amount >= 0 AND deductible_tax_amount <= tax_amount",
            name="ck_supplier_invoice_tax_breakdowns_deductible_valid",
        ),
        sa.ForeignKeyConstraint(["supplier_invoice_id"], ["supplier_invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supplier_invoice_id",
            "position",
            name="uq_supplier_invoice_tax_breakdowns_position",
        ),
    )

    op.create_table(
        "supplier_invoice_reception_sequences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_number", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "last_number >= 0",
            name="ck_supplier_invoice_reception_sequences_last_number_nonnegative",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO supplier_invoice_reception_sequences (id, last_number) VALUES (1, 0)")


def downgrade():
    op.drop_table("supplier_invoice_reception_sequences")
    op.drop_table("supplier_invoice_tax_breakdowns")
    op.drop_index(
        "ix_supplier_invoices_supplier_tax_id_invoice_number",
        table_name="supplier_invoices",
    )
    op.drop_table("supplier_invoices")
