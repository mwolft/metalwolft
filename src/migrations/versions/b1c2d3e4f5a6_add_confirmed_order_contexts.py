"""add immutable confirmed order contexts

Revision ID: b1c2d3e4f5a6
Revises: a5b6c7d8e9f0
Create Date: 2026-09-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "confirmed_order_contexts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="web_checkout"),
        sa.Column("quote_snapshot", sa.JSON(), nullable=False),
        sa.Column("customer_snapshot", sa.JSON(), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False, server_default="confirmed"),
        sa.Column("payment_reference", sa.String(length=255), nullable=True),
        sa.Column("provider_identifiers", sa.JSON(), nullable=True),
        sa.Column("payment_confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("payment_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("confirmed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("confirmed_by", sa.String(length=255), nullable=True),
        sa.Column("source_checkout_session_id", sa.Integer(), nullable=True),
        sa.Column("source_manual_draft_id", sa.Integer(), nullable=True),
        sa.Column("internal_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "source IN ('web_checkout', 'admin_external')",
            name="ck_confirmed_order_contexts_source_valid",
        ),
        sa.CheckConstraint(
            "payment_method IN ('stripe', 'paypal', 'bank_transfer', 'cash', 'external_other')",
            name="ck_confirmed_order_contexts_payment_method_valid",
        ),
        sa.CheckConstraint(
            "payment_status = 'confirmed'",
            name="ck_confirmed_order_contexts_payment_status_confirmed",
        ),
        sa.CheckConstraint(
            "currency = 'EUR'",
            name="ck_confirmed_order_contexts_currency_eur",
        ),
        sa.CheckConstraint(
            "payment_amount >= 0",
            name="ck_confirmed_order_contexts_payment_amount_nonnegative",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["source_checkout_session_id"], ["checkout_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
        sa.UniqueConstraint("source_checkout_session_id"),
        sa.UniqueConstraint("source_manual_draft_id"),
    )


def downgrade():
    op.drop_table("confirmed_order_contexts")
