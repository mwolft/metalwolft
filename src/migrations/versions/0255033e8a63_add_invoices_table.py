"""Add invoices table

Revision ID: 0255033e8a63
Revises: 8980a24a8f42
Create Date: 2024-12-13 16:43:04.403802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0255033e8a63'
down_revision = '8980a24a8f42'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('invoice_number', sa.String(length=50), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('pdf_path', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('client_name', sa.String(length=255), nullable=False),
    sa.Column('client_address', sa.String(length=255), nullable=False),
    sa.Column('client_cif', sa.String(length=50), nullable=True),
    sa.Column('order_details', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('invoice_number')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('invoices')
    # ### end Alembic commands ###