"""add verifactu records table

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'verifactu_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('mode', sa.String(length=30), nullable=False),
        sa.Column('record_type', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('schema_version', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('invoice_issued_at', sa.DateTime(), nullable=False),
        sa.Column('invoice_snapshot_hash', sa.String(length=64), nullable=False),
        sa.Column('record_payload', sa.JSON(), nullable=False),
        sa.Column('record_payload_hash', sa.String(length=64), nullable=False),
        sa.Column('fingerprint', sa.String(length=128), nullable=True),
        sa.Column('fingerprint_algorithm', sa.String(length=100), nullable=True),
        sa.Column('fingerprint_status', sa.String(length=30), nullable=False),
        sa.Column('system_id', sa.String(length=100), nullable=False),
        sa.Column('software_name', sa.String(length=120), nullable=False),
        sa.Column('software_version', sa.String(length=50), nullable=False),
        sa.Column('issuer_tax_id', sa.String(length=50), nullable=False),
        sa.Column('recipient_tax_id', sa.String(length=50), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'invoice_id',
            'record_type',
            name='uq_verifactu_records_invoice_record_type',
        ),
    )
    op.create_index(
        'ix_verifactu_records_invoice_id',
        'verifactu_records',
        ['invoice_id'],
        unique=False,
    )


def downgrade():
    op.drop_index('ix_verifactu_records_invoice_id', table_name='verifactu_records')
    op.drop_table('verifactu_records')
