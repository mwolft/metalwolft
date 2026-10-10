"""Persist development-only customer photo incentive simulations.

Revision ID: d0e1f2a3b4c5
Revises: b8c9d0e1f2a3
"""

from alembic import op
import sqlalchemy as sa


revision = "d0e1f2a3b4c5"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "customer_photo_requests",
        sa.Column("is_simulation", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_constraint("ck_customer_photo_requests_amount", "customer_photo_requests", type_="check")
    op.create_check_constraint(
        "ck_customer_photo_requests_amount",
        "customer_photo_requests",
        "(mode = 'free' AND offered_amount = 0 AND NOT is_simulation) OR "
        "(mode = 'incentive' AND is_simulation AND offered_amount = 0) OR "
        "(mode = 'incentive' AND NOT is_simulation AND offered_amount = 20)",
    )
    op.create_check_constraint(
        "ck_customer_photo_requests_simulation_no_refund",
        "customer_photo_requests",
        "NOT is_simulation OR status != 'refund_pending'",
    )


def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM customer_photo_requests WHERE is_simulation LIMIT 1")).first():
        raise RuntimeError("No se puede retirar la marca de simulación mientras existan solicitudes simuladas.")
    op.drop_constraint("ck_customer_photo_requests_simulation_no_refund", "customer_photo_requests", type_="check")
    op.drop_constraint("ck_customer_photo_requests_amount", "customer_photo_requests", type_="check")
    op.create_check_constraint(
        "ck_customer_photo_requests_amount",
        "customer_photo_requests",
        "(mode = 'free' AND offered_amount = 0) OR "
        "(mode = 'incentive' AND offered_amount = 20)",
    )
    op.drop_column("customer_photo_requests", "is_simulation")
