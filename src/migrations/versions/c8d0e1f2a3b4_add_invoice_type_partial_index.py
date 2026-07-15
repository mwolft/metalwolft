"""add invoice type partial unique index

Revision ID: c8d0e1f2a3b4
Revises: b7c9d1e2f3a4
Create Date: 2026-07-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d0e1f2a3b4'
down_revision = 'b7c9d1e2f3a4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invoices', sa.Column('invoice_type', sa.String(length=20), nullable=True))
    op.create_index(
        'uq_invoices_one_ordinary_per_order',
        'invoices',
        ['order_id'],
        unique=True,
        postgresql_where=sa.text("invoice_type = 'ordinary' AND order_id IS NOT NULL"),
    )


def downgrade():
    op.drop_index('uq_invoices_one_ordinary_per_order', table_name='invoices')
    op.drop_column('invoices', 'invoice_type')
