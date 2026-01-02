"""add created_at to users

Revision ID: 8939fd4f21c1
Revises: 19269d35ed5e
Create Date: 2026-01-01 08:46:38.424890

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8939fd4f21c1'
down_revision = '19269d35ed5e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False
        )
    )


def downgrade():
    op.drop_column('users', 'created_at')
