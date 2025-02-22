"""Añadidos campos has_abatible y has_door_model en Products y client_phone en Invoices

Revision ID: 35bd73476ddd
Revises: eb905ec09c1c
Create Date: 2025-02-20 03:47:42.414314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35bd73476ddd'
down_revision = 'eb905ec09c1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_phone', sa.String(length=50), nullable=True))

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('has_abatible', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('has_door_model', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('has_door_model')
        batch_op.drop_column('has_abatible')

    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_column('client_phone')

    # ### end Alembic commands ###
