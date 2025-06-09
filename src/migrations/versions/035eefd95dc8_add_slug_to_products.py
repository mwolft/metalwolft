"""Add slug to Products

Revision ID: 035eefd95dc8
Revises: 35bd73476ddd
Create Date: 2025-06-08 16:39:18.982504

"""
from alembic import op
import sqlalchemy as sa
from slugify import slugify

# revision identifiers, used by Alembic.
revision = '035eefd95dc8'
down_revision = '35bd73476ddd'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Añadimos la columna slug como NULLABLE
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=120), nullable=True))

    # 2) Rellenamos slug para cada producto existente
    bind = op.get_bind()
    results = bind.execute(sa.text("SELECT id, nombre FROM products")).fetchall()
    for prod_id, nombre in results:
        slug = slugify(nombre)
        bind.execute(
            sa.text("UPDATE products SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": prod_id}
        )

    # 3) Hacemos slug NOT NULL y le ponemos la restricción UNIQUE
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column('slug', nullable=False)
        batch_op.create_unique_constraint('uq_products_slug', ['slug'])


def downgrade():
    # Para revertir bajamos la restricción y eliminamos la columna
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('uq_products_slug', type_='unique')
        batch_op.drop_column('slug')
