"""make invoice pdf path nullable

Revision ID: d9e0f1a2b3c4
Revises: c8d0e1f2a3b4
Create Date: 2026-07-15 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9e0f1a2b3c4'
down_revision = 'c8d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'invoices',
        'pdf_path',
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        'invoices',
        'pdf_path',
        existing_type=sa.String(length=255),
        nullable=False,
    )
