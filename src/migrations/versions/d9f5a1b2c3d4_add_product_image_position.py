"""Add an optional, non-destructive product image position.

Revision ID: d9f5a1b2c3d4
Revises: c8e4f0a2b6d9
"""

from alembic import op
import sqlalchemy as sa


revision = "d9f5a1b2c3d4"
down_revision = "c8e4f0a2b6d9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("product_images", sa.Column("position", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("product_images", "position")
