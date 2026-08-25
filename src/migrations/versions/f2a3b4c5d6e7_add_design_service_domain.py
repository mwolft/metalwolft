"""add design service domain

Revision ID: f2a3b4c5d6e7
Revises: f0a1b2c3d4e5
Create Date: 2026-08-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f2a3b4c5d6e7"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "design_service_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("base_price_gross", sa.Numeric(12, 2), nullable=False, server_default="24.95"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("lead_time_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("id = 1", name="ck_design_service_config_singleton"),
        sa.CheckConstraint("base_price_gross > 0", name="ck_design_service_config_price_positive"),
        sa.CheckConstraint("currency = 'EUR'", name="ck_design_service_config_currency_eur"),
        sa.CheckConstraint("lead_time_hours > 0", name="ck_design_service_config_lead_time_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO design_service_config (id, is_active, base_price_gross, currency, lead_time_hours) "
            "VALUES (1, true, 24.95, 'EUR', 24)"
        )
    )
    op.create_table(
        "design_service_price_tiers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("min_design_count", sa.Integer(), nullable=False),
        sa.Column("unit_price_gross", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("min_design_count > 1", name="ck_design_price_tier_min_count"),
        sa.CheckConstraint("unit_price_gross > 0", name="ck_design_price_tier_unit_positive"),
        sa.ForeignKeyConstraint(["config_id"], ["design_service_config.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("min_design_count"),
    )
    op.execute(
        sa.text(
            "INSERT INTO design_service_price_tiers (config_id, min_design_count, unit_price_gross) VALUES "
            "(1, 2, 22.45), (1, 3, 19.95), (1, 4, 17.95)"
        )
    )
    with op.batch_alter_table("order_details") as batch_op:
        batch_op.add_column(sa.Column("line_type", sa.String(24), nullable=False, server_default="physical"))
        batch_op.create_check_constraint(
            "ck_order_details_line_type_valid",
            "line_type IN ('physical', 'design_service')",
        )
    op.create_table(
        "design_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(32), nullable=False),
        sa.Column("creation_key", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("subtotal_gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("pricing_tier_min_design_count", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("lead_time_hours", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending_payment"),
        sa.Column("requested_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("result_storage_key", sa.String(500), nullable=True),
        sa.Column("result_filename", sa.String(255), nullable=True),
        sa.Column("result_mime", sa.String(100), nullable=True),
        sa.Column("result_size", sa.Integer(), nullable=True),
        sa.Column("result_sha256", sa.String(64), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending_payment', 'pending', 'in_progress', 'delivered', 'cancelled')",
            name="ck_design_requests_status_valid",
        ),
        sa.CheckConstraint("subtotal_gross > 0", name="ck_design_requests_subtotal_positive"),
        sa.CheckConstraint("price_gross > 0", name="ck_design_requests_price_positive"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_design_requests_discount_nonnegative"),
        sa.CheckConstraint("currency = 'EUR'", name="ck_design_requests_currency_eur"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
        sa.UniqueConstraint("order_id"),
        sa.UniqueConstraint("user_id", "creation_key", name="uq_design_requests_user_creation_key"),
    )
    op.create_index("ix_design_requests_user_id", "design_requests", ["user_id"])
    op.create_table(
        "design_request_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("design_request_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("width_cm", sa.Numeric(8, 2), nullable=False),
        sa.Column("height_cm", sa.Numeric(8, 2), nullable=False),
        sa.Column("order_detail_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("width_cm > 0", name="ck_design_request_items_width_positive"),
        sa.CheckConstraint("height_cm > 0", name="ck_design_request_items_height_positive"),
        sa.ForeignKeyConstraint(["design_request_id"], ["design_requests.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["order_detail_id"], ["order_details.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_detail_id"),
        sa.UniqueConstraint(
            "design_request_id", "product_id", "width_cm", "height_cm",
            name="uq_design_request_items_model_dimensions",
        ),
    )
    op.create_index("ix_design_request_items_request_id", "design_request_items", ["design_request_id"])
    with op.batch_alter_table("checkout_sessions") as batch_op:
        batch_op.add_column(sa.Column("design_request_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_checkout_sessions_design_request_id",
            "design_requests",
            ["design_request_id"],
            ["id"],
        )
        batch_op.create_index("ix_checkout_sessions_design_request_id", ["design_request_id"])


def downgrade():
    with op.batch_alter_table("checkout_sessions") as batch_op:
        batch_op.drop_index("ix_checkout_sessions_design_request_id")
        batch_op.drop_constraint("fk_checkout_sessions_design_request_id", type_="foreignkey")
        batch_op.drop_column("design_request_id")
    op.drop_index("ix_design_request_items_request_id", table_name="design_request_items")
    op.drop_table("design_request_items")
    op.drop_index("ix_design_requests_user_id", table_name="design_requests")
    op.drop_table("design_requests")
    with op.batch_alter_table("order_details") as batch_op:
        batch_op.drop_constraint("ck_order_details_line_type_valid", type_="check")
        batch_op.drop_column("line_type")
    op.drop_table("design_service_price_tiers")
    op.drop_table("design_service_config")
