"""Persist customer opposition to future photo-promotion invitations.

Revision ID: c2d3e4f5a6b7
Revises: e1f2a3b4c5d6
"""

from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer_photo_promotion_opt_outs",
        sa.Column("email_hash", sa.String(64), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source IN ('customer', 'admin')", name="ck_customer_photo_promotion_opt_outs_source"),
    )


def downgrade():
    op.drop_table("customer_photo_promotion_opt_outs")
