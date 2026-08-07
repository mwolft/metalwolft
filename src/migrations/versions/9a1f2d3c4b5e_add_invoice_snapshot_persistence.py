"""add invoice snapshot persistence

Revision ID: 9a1f2d3c4b5e
Revises: 8f2d9b7c1a4e
Create Date: 2026-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a1f2d3c4b5e'
down_revision = '8f2d9b7c1a4e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invoices', sa.Column('invoice_snapshot', sa.JSON(), nullable=True))
    op.add_column('invoices', sa.Column('invoice_snapshot_schema_version', sa.Integer(), nullable=True))
    op.add_column('invoices', sa.Column('invoice_snapshot_hash', sa.String(length=64), nullable=True))
    op.add_column('invoices', sa.Column('issued_at', sa.DateTime(), nullable=True))
    op.add_column('invoices', sa.Column('issuance_source', sa.String(length=50), nullable=True))
    op.add_column('invoices', sa.Column('issued_by', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('invoices', 'issued_by')
    op.drop_column('invoices', 'issuance_source')
    op.drop_column('invoices', 'issued_at')
    op.drop_column('invoices', 'invoice_snapshot_hash')
    op.drop_column('invoices', 'invoice_snapshot_schema_version')
    op.drop_column('invoices', 'invoice_snapshot')
