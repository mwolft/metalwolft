"""Add shared photo request limits and recoverable upload reservations.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
"""

from alembic import op
import sqlalchemy as sa


revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer_photo_rate_limits",
        sa.Column("bucket_key", sa.String(64), primary_key=True),
        sa.Column("window_started_at", sa.DateTime(), nullable=False),
        sa.Column("hits", sa.Integer(), nullable=False),
    )
    op.create_table(
        "customer_photo_upload_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("customer_photo_requests.id"), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("storage_key", name="uq_customer_photo_upload_attempts_storage_key"),
    )
    op.create_index(
        "ix_customer_photo_upload_attempts_request_id",
        "customer_photo_upload_attempts", ["request_id"],
    )
    op.create_index(
        "ix_customer_photo_upload_attempts_created_at",
        "customer_photo_upload_attempts", ["created_at"],
    )


def downgrade():
    op.drop_index("ix_customer_photo_upload_attempts_created_at", table_name="customer_photo_upload_attempts")
    op.drop_index("ix_customer_photo_upload_attempts_request_id", table_name="customer_photo_upload_attempts")
    op.drop_table("customer_photo_upload_attempts")
    op.drop_table("customer_photo_rate_limits")
