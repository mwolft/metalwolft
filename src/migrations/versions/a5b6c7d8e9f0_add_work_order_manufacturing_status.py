"""add operational manufacturing status to work orders

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-09-09 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a5b6c7d8e9f0"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("work_orders", sa.Column("manufactured_at", sa.DateTime(), nullable=True))
    op.add_column("work_orders", sa.Column("manufactured_by", sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column("work_orders", "manufactured_by")
    op.drop_column("work_orders", "manufactured_at")
