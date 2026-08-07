"""add invoice rectification fields

Revision ID: b2c3d4e5f6a7
Revises: a2b3c4d5e6f7
Create Date: 2026-08-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invoices', sa.Column('original_invoice_id', sa.Integer(), nullable=True))
    op.add_column('invoices', sa.Column('rectification_type', sa.String(length=30), nullable=True))
    op.add_column('invoices', sa.Column('rectification_reason', sa.String(length=50), nullable=True))

    op.create_index(
        'ix_invoices_original_invoice_id',
        'invoices',
        ['original_invoice_id'],
        unique=False,
    )
    op.create_foreign_key(
        'fk_invoices_original_invoice_id',
        'invoices',
        'invoices',
        ['original_invoice_id'],
        ['id'],
    )
    op.create_check_constraint(
        'ck_invoices_rectification_consistency',
        'invoices',
        "("
        "invoice_type IS NULL AND original_invoice_id IS NULL AND "
        "rectification_type IS NULL AND rectification_reason IS NULL"
        ") OR ("
        "invoice_type = 'ordinary' AND original_invoice_id IS NULL AND "
        "rectification_type IS NULL AND rectification_reason IS NULL"
        ") OR ("
        "invoice_type = 'corrective' AND original_invoice_id IS NOT NULL AND "
        "original_invoice_id != id AND rectification_type IS NOT NULL AND "
        "rectification_reason IS NOT NULL"
        ")",
    )
    op.create_check_constraint(
        'ck_invoices_invoice_type_valid',
        'invoices',
        "invoice_type IS NULL OR invoice_type IN ('ordinary', 'corrective')",
    )
    op.create_check_constraint(
        'ck_invoices_rectification_type_valid',
        'invoices',
        "rectification_type IS NULL OR rectification_type IN ('differences', 'substitution')",
    )
    op.create_check_constraint(
        'ck_invoices_rectification_reason_valid',
        'invoices',
        "rectification_reason IS NULL OR rectification_reason IN ("
        "'invoice_error', 'return', 'price_error', 'shipping_error', 'other')",
    )
    op.create_check_constraint(
        'ck_invoices_original_invoice_not_self',
        'invoices',
        'original_invoice_id IS NULL OR original_invoice_id != id',
    )


def downgrade():
    op.drop_index('ix_invoices_original_invoice_id', table_name='invoices')
    op.drop_constraint('ck_invoices_original_invoice_not_self', 'invoices', type_='check')
    op.drop_constraint('ck_invoices_rectification_reason_valid', 'invoices', type_='check')
    op.drop_constraint('ck_invoices_rectification_type_valid', 'invoices', type_='check')
    op.drop_constraint('ck_invoices_invoice_type_valid', 'invoices', type_='check')
    op.drop_constraint('ck_invoices_rectification_consistency', 'invoices', type_='check')
    op.drop_constraint('fk_invoices_original_invoice_id', 'invoices', type_='foreignkey')
    op.drop_column('invoices', 'rectification_reason')
    op.drop_column('invoices', 'rectification_type')
    op.drop_column('invoices', 'original_invoice_id')
