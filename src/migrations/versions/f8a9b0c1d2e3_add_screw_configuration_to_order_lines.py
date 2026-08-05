"""add screw configuration to cart and order lines

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-08-04 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "f8a9b0c1d2e3"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


INTERIOR_HOLES = "Sin obra: con agujeros interiores"
FRONT_PLATES = "Sin obra: con pletinas"


def _add_screw_columns(table_name):
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "screw_option",
                sa.String(length=20),
                nullable=False,
                server_default="standard",
            )
        )
        batch_op.add_column(sa.Column("screw_length_mm", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "screw_supplement",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def _backfill_standard_lengths(table_name):
    table = sa.table(
        table_name,
        sa.column("anclaje", sa.String()),
        sa.column("screw_length_mm", sa.Integer()),
    )
    op.execute(
        table.update()
        .where(table.c.anclaje == INTERIOR_HOLES)
        .values(screw_length_mm=80)
    )
    op.execute(
        table.update()
        .where(table.c.anclaje == FRONT_PLATES)
        .values(screw_length_mm=70)
    )


def upgrade():
    for table_name in ("cart", "order_details"):
        _add_screw_columns(table_name)
        _backfill_standard_lengths(table_name)


def downgrade():
    for table_name in ("order_details", "cart"):
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.drop_column("screw_supplement")
            batch_op.drop_column("screw_length_mm")
            batch_op.drop_column("screw_option")
