"""add invoice email status fields

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invoices', sa.Column('email_status', sa.String(length=20), nullable=True))
    op.add_column('invoices', sa.Column('email_sent_at', sa.DateTime(), nullable=True))
    op.add_column('invoices', sa.Column('email_last_error', sa.Text(), nullable=True))
    op.add_column(
        'invoices',
        sa.Column('email_attempts', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade():
    op.drop_column('invoices', 'email_attempts')
    op.drop_column('invoices', 'email_last_error')
    op.drop_column('invoices', 'email_sent_at')
    op.drop_column('invoices', 'email_status')
