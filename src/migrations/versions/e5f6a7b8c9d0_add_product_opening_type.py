"""Add an authoritative opening type to products.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "opening_type",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'fixed'"),
            )
        )
        batch_op.create_check_constraint(
            "ck_products_opening_type",
            "opening_type IN ('fixed', 'hinged')",
        )


def downgrade():
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_constraint("ck_products_opening_type", type_="check")
        batch_op.drop_column("opening_type")
