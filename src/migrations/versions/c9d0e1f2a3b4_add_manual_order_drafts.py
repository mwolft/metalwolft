"""add manual order drafts

Revision ID: c9d0e1f2a3b4
Revises: b1c2d3e4f5a6
Create Date: 2026-09-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c9d0e1f2a3b4"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "manual_order_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("customer_draft", sa.JSON(), nullable=True),
        sa.Column("discount_code", sa.String(length=50), nullable=True),
        sa.Column("estimated_delivery_at", sa.Date(), nullable=True),
        sa.Column("estimated_delivery_note", sa.String(length=255), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("payment_reference", sa.String(length=255), nullable=True),
        sa.Column("payment_confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("payment_note", sa.Text(), nullable=True),
        sa.Column("internal_note", sa.Text(), nullable=True),
        sa.Column("last_quote_snapshot", sa.JSON(), nullable=True),
        sa.Column("quote_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("issuance_key", sa.String(length=36), nullable=True),
        sa.Column("issued_order_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('draft', 'issued', 'cancelled')",
            name="ck_manual_order_drafts_status_valid",
        ),
        sa.CheckConstraint(
            "payment_method IS NULL OR payment_method IN "
            "('bank_transfer', 'cash', 'external_other')",
            name="ck_manual_order_drafts_payment_method_valid",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["issued_order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issuance_key", name="uq_manual_order_drafts_issuance_key"),
        sa.UniqueConstraint("issued_order_id", name="uq_manual_order_drafts_issued_order_id"),
    )
    op.create_index(
        "ix_manual_order_drafts_user_status",
        "manual_order_drafts",
        ["user_id", "status"],
        unique=False,
    )

    op.create_table(
        "manual_order_draft_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("draft_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("alto", sa.Float(), nullable=True),
        sa.Column("ancho", sa.Float(), nullable=True),
        sa.Column("anclaje", sa.String(length=50), nullable=True),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("screw_option", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_manual_order_draft_lines_quantity_positive",
        ),
        sa.CheckConstraint(
            "position >= 0",
            name="ck_manual_order_draft_lines_position_nonnegative",
        ),
        sa.ForeignKeyConstraint(["draft_id"], ["manual_order_drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("draft_id", "position", name="uq_manual_order_draft_lines_position"),
    )

    with op.batch_alter_table("confirmed_order_contexts") as batch_op:
        batch_op.create_foreign_key(
            "fk_confirmed_order_contexts_source_manual_draft_id",
            "manual_order_drafts",
            ["source_manual_draft_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("confirmed_order_contexts") as batch_op:
        batch_op.drop_constraint(
            "fk_confirmed_order_contexts_source_manual_draft_id",
            type_="foreignkey",
        )

    op.drop_table("manual_order_draft_lines")
    op.drop_index("ix_manual_order_drafts_user_status", table_name="manual_order_drafts")
    op.drop_table("manual_order_drafts")
