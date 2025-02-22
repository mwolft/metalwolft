"""Add precio_rebajado and porcentaje_rebaja to Products

Revision ID: eb905ec09c1c
Revises: 
Create Date: 2025-01-20 10:27:37.318182

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb905ec09c1c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('precio_rebajado', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('porcentaje_rebaja', sa.Integer(), nullable=True))
        batch_op.drop_column('model_3d_url')
        batch_op.drop_column('additional_model_3d_url')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('additional_model_3d_url', sa.VARCHAR(length=300), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('model_3d_url', sa.VARCHAR(length=300), autoincrement=False, nullable=True))
        batch_op.drop_column('porcentaje_rebaja')
        batch_op.drop_column('precio_rebajado')

    # ### end Alembic commands ###
