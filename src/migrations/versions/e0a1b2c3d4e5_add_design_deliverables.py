"""Add private per-design deliverables without moving legacy results.

Revision ID: e0a1b2c3d4e5
Revises: d9f5a1b2c3d4
"""

from alembic import op
import sqlalchemy as sa


revision = "e0a1b2c3d4e5"
down_revision = "d9f5a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("design_requests", sa.Column("customer_message", sa.Text(), nullable=True))
    op.create_table(
        "design_deliverables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("design_request_item_id", sa.Integer(), sa.ForeignKey("design_request_items.id"), nullable=False),
        sa.Column("kind", sa.String(8), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False, unique=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("kind IN ('glb', 'image', 'pdf')", name="ck_design_deliverables_kind"),
        sa.CheckConstraint("size_bytes > 0", name="ck_design_deliverables_size"),
    )
    op.create_index(
        "ix_design_deliverables_item_active", "design_deliverables", ["design_request_item_id", "active"]
    )


def downgrade():
    # Refuse destructive rollback; revert application code while retaining the additive schema.
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM design_deliverables LIMIT 1")).first():
        raise RuntimeError("Export and preserve design deliverables before schema downgrade.")
    if connection.execute(sa.text("SELECT 1 FROM design_requests WHERE customer_message IS NOT NULL LIMIT 1")).first():
        raise RuntimeError("Export and preserve customer messages before schema downgrade.")
    op.drop_index("ix_design_deliverables_item_active", table_name="design_deliverables")
    op.drop_table("design_deliverables")
    op.drop_column("design_requests", "customer_message")
