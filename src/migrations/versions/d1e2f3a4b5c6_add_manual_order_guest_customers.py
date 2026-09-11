"""allow guest customers in manual order drafts

Revision ID: d1e2f3a4b5c6
Revises: c9d0e1f2a3b4
Create Date: 2026-09-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d1e2f3a4b5c6"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

    with op.batch_alter_table("manual_order_drafts") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.add_column(
            sa.Column(
                "customer_mode",
                sa.String(length=24),
                nullable=True,
                server_default=sa.text("'registered_user'"),
            )
        )

    op.execute(
        "UPDATE manual_order_drafts "
        "SET customer_mode = 'registered_user' "
        "WHERE customer_mode IS NULL"
    )

    with op.batch_alter_table("manual_order_drafts") as batch_op:
        batch_op.alter_column(
            "customer_mode",
            existing_type=sa.String(length=24),
            nullable=False,
            server_default=sa.text("'registered_user'"),
        )
        batch_op.create_check_constraint(
            "ck_manual_order_drafts_customer_mode_valid",
            "customer_mode IN ('registered_user', 'manual_customer')",
        )
        batch_op.create_check_constraint(
            "ck_manual_order_drafts_customer_mode_user",
            "(customer_mode = 'registered_user' AND user_id IS NOT NULL) OR "
            "(customer_mode = 'manual_customer' AND user_id IS NULL)",
        )


def downgrade():
    with op.batch_alter_table("manual_order_drafts") as batch_op:
        batch_op.drop_constraint(
            "ck_manual_order_drafts_customer_mode_user",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_manual_order_drafts_customer_mode_valid",
            type_="check",
        )
        batch_op.drop_column("customer_mode")
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
