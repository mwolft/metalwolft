"""add checkout_sessions table

Revision ID: c4f7a8b91d2e
Revises: 8939fd4f21c1
Create Date: 2026-04-20 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4f7a8b91d2e'
down_revision = '8939fd4f21c1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'checkout_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('payment_intent_id', sa.String(length=255), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('shipping_cost', sa.Float(), nullable=False),
        sa.Column('discount_code', sa.String(length=50), nullable=True),
        sa.Column('discount_percent', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('quote_snapshot', sa.JSON(), nullable=False),
        sa.Column('customer_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id'),
        sa.UniqueConstraint('payment_intent_id')
    )
    op.create_index(op.f('ix_checkout_sessions_idempotency_key'), 'checkout_sessions', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_checkout_sessions_payment_intent_id'), 'checkout_sessions', ['payment_intent_id'], unique=True)
    op.create_index(op.f('ix_checkout_sessions_user_id'), 'checkout_sessions', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_checkout_sessions_user_id'), table_name='checkout_sessions')
    op.drop_index(op.f('ix_checkout_sessions_payment_intent_id'), table_name='checkout_sessions')
    op.drop_index(op.f('ix_checkout_sessions_idempotency_key'), table_name='checkout_sessions')
    op.drop_table('checkout_sessions')
