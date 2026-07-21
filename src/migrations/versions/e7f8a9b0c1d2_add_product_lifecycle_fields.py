"""add product lifecycle fields

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'e7f8a9b0c1d2'
down_revision = 'd6e7f8a9b0c1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'products',
        sa.Column(
            'published',
            sa.Boolean(),
            server_default=sa.true(),
            nullable=True,
        ),
    )
    op.add_column(
        'products',
        sa.Column(
            'available_for_sale',
            sa.Boolean(),
            server_default=sa.true(),
            nullable=True,
        ),
    )

    products = sa.table(
        'products',
        sa.column('published', sa.Boolean()),
        sa.column('available_for_sale', sa.Boolean()),
    )
    op.execute(
        products.update()
        .where(
            sa.or_(
                products.c.published.is_(None),
                products.c.available_for_sale.is_(None),
            )
        )
        .values(published=True, available_for_sale=True)
    )

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column(
            'published',
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        )
        batch_op.alter_column(
            'available_for_sale',
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        )
        batch_op.create_check_constraint(
            'ck_products_published_available_for_sale',
            'published OR NOT available_for_sale',
        )


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint(
            'ck_products_published_available_for_sale',
            type_='check',
        )
        batch_op.drop_column('available_for_sale')
        batch_op.drop_column('published')
