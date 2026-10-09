"""Add private post-delivery customer photo requests.

Revision ID: f6a7b8c9d0e1
Revises: e2f3a4b5c6d7
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer_photo_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("offered_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(), nullable=False),
        sa.Column("token_revoked_at", sa.DateTime(), nullable=True),
        sa.Column("terms_version", sa.String(50), nullable=False),
        sa.Column("terms_text", sa.Text(), nullable=False),
        sa.Column("terms_url", sa.String(500), nullable=True),
        sa.Column("offered_consent_text", sa.Text(), nullable=False),
        sa.Column("email_options", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("email_sent_at", sa.DateTime(), nullable=True),
        sa.Column("email_failed_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("commercial_consent", sa.Boolean(), nullable=True),
        sa.Column("consent_text", sa.Text(), nullable=True),
        sa.Column("consent_version", sa.String(50), nullable=True),
        sa.Column("consent_at", sa.DateTime(), nullable=True),
        sa.Column("consent_evidence", sa.JSON(), nullable=True),
        sa.Column("consent_revoked_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("mode IN ('free', 'incentive')", name="ck_customer_photo_requests_mode"),
        sa.CheckConstraint(
            "status IN ('offered', 'received', 'approved', 'rejected', 'refund_pending', 'revoked')",
            name="ck_customer_photo_requests_status",
        ),
        sa.CheckConstraint(
            "(mode = 'free' AND offered_amount = 0) OR "
            "(mode = 'incentive' AND offered_amount = 20)",
            name="ck_customer_photo_requests_amount",
        ),
        sa.UniqueConstraint("order_id", name="uq_customer_photo_requests_order_id"),
        sa.UniqueConstraint("token_hash", name="uq_customer_photo_requests_token_hash"),
    )
    op.create_table(
        "customer_photo_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("customer_photo_requests.id"), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(30), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("review_status", sa.String(20), nullable=False),
        sa.UniqueConstraint("request_id", "sha256", name="uq_customer_photo_images_hash"),
        sa.UniqueConstraint("storage_key", name="uq_customer_photo_images_storage_key"),
    )
    op.create_index("ix_customer_photo_images_request_id", "customer_photo_images", ["request_id"])


def downgrade():
    op.drop_index("ix_customer_photo_images_request_id", table_name="customer_photo_images")
    op.drop_table("customer_photo_images")
    op.drop_table("customer_photo_requests")
