"""add invoice fiscal submissions table

Revision ID: e6f7a8b9c0d1
Revises: d9e0f1a2b3c4
Create Date: 2026-07-15 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e6f7a8b9c0d1'
down_revision = 'd9e0f1a2b3c4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'invoice_fiscal_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('response_at', sa.DateTime(), nullable=True),
        sa.Column('request_payload', sa.JSON(), nullable=True),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('response_code', sa.String(length=100), nullable=True),
        sa.Column('response_message', sa.Text(), nullable=True),
        sa.Column('verification_csv', sa.String(length=255), nullable=True),
        sa.Column('verification_url', sa.String(length=500), nullable=True),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'invoice_id',
            'provider',
            'attempt_number',
            name='uq_invoice_fiscal_submissions_invoice_provider_attempt',
        ),
    )
    op.create_index(
        'ix_invoice_fiscal_submissions_invoice_id',
        'invoice_fiscal_submissions',
        ['invoice_id'],
    )


def downgrade():
    op.drop_index(
        'ix_invoice_fiscal_submissions_invoice_id',
        table_name='invoice_fiscal_submissions',
    )
    op.drop_table('invoice_fiscal_submissions')
