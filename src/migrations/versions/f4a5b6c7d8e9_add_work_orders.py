"""add immutable manufacturing work orders

Revision ID: f4a5b6c7d8e9
Revises: f2a3b4c5d6e7
Create Date: 2026-09-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f4a5b6c7d8e9"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.CheckConstraint("schema_version > 0", name="ck_work_orders_schema_version_positive"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_work_orders_order_id"),
    )


def downgrade():
    op.drop_table("work_orders")
