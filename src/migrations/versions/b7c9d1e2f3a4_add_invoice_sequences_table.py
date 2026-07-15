"""add invoice sequences table

Revision ID: b7c9d1e2f3a4
Revises: 9a1f2d3c4b5e
Create Date: 2026-07-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c9d1e2f3a4'
down_revision = '9a1f2d3c4b5e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'invoice_sequences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series', sa.String(length=10), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('last_number', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'series',
            'fiscal_year',
            name='uq_invoice_sequences_series_fiscal_year',
        ),
    )


def downgrade():
    op.drop_table('invoice_sequences')
