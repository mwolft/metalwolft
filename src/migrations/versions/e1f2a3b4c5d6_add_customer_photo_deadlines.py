"""Freeze delivery and participation dates for new customer photo requests.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
"""

from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("customer_photo_requests", sa.Column("actual_delivery_on", sa.Date(), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("participation_deadline_on", sa.Date(), nullable=True))
    op.add_column("customer_photo_requests", sa.Column("receipt_accredited_on", sa.Date(), nullable=True))
    op.create_table(
        "customer_photo_followup_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("customer_photo_requests.id"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("received_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.CheckConstraint("kind IN ('correction_requested', 'correction_received')", name="ck_customer_photo_followup_notes_kind"),
    )
    op.create_index("ix_customer_photo_followup_notes_request_id", "customer_photo_followup_notes", ["request_id"])


def downgrade():
    op.drop_index("ix_customer_photo_followup_notes_request_id", table_name="customer_photo_followup_notes")
    op.drop_table("customer_photo_followup_notes")
    op.drop_column("customer_photo_requests", "receipt_accredited_on")
    op.drop_column("customer_photo_requests", "participation_deadline_on")
    op.drop_column("customer_photo_requests", "actual_delivery_on")
