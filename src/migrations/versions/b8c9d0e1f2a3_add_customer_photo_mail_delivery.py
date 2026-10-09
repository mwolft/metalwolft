"""Add mail delivery and reconciliation metadata for customer photographs.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
"""

from alembic import op
import sqlalchemy as sa


revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("customer_photo_requests", sa.Column("photo_count", sa.Integer(), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("delivery_status", sa.String(20), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("delivery_attempt_id", sa.String(32), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("delivery_started_at", sa.DateTime(), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("delivery_message_id", sa.String(255), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("mailbox_confirmed_at", sa.DateTime(), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("mailbox_confirmed_by", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_customer_photo_requests_delivery_attempt", "customer_photo_requests", ["delivery_attempt_id"])


def downgrade():
    op.drop_constraint("uq_customer_photo_requests_delivery_attempt", "customer_photo_requests", type_="unique")
    for name in ("mailbox_confirmed_by", "mailbox_confirmed_at", "delivery_message_id", "delivery_started_at", "delivery_attempt_id", "delivery_status", "photo_count"):
        op.drop_column("customer_photo_requests", name)
