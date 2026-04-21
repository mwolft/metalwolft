"""make checkout_sessions provider agnostic

Revision ID: 8f2d9b7c1a4e
Revises: c4f7a8b91d2e
Create Date: 2026-04-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = '8f2d9b7c1a4e'
down_revision = 'c4f7a8b91d2e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('checkout_sessions', sa.Column('payment_provider', sa.String(length=50), nullable=True))
    op.add_column('checkout_sessions', sa.Column('provider_order_id', sa.String(length=255), nullable=True))
    op.add_column('checkout_sessions', sa.Column('provider_capture_id', sa.String(length=255), nullable=True))
    op.add_column('checkout_sessions', sa.Column('provider_status', sa.String(length=100), nullable=True))
    op.add_column('checkout_sessions', sa.Column('public_checkout_token', sa.String(length=64), nullable=True))

    op.create_index(op.f('ix_checkout_sessions_provider_order_id'), 'checkout_sessions', ['provider_order_id'], unique=False)
    op.create_index(op.f('ix_checkout_sessions_provider_capture_id'), 'checkout_sessions', ['provider_capture_id'], unique=False)
    op.create_index(op.f('ix_checkout_sessions_public_checkout_token'), 'checkout_sessions', ['public_checkout_token'], unique=True)

    bind = op.get_bind()
    checkout_sessions = sa.table(
        'checkout_sessions',
        sa.column('id', sa.Integer()),
        sa.column('payment_intent_id', sa.String(length=255)),
        sa.column('status', sa.String(length=50)),
        sa.column('payment_provider', sa.String(length=50)),
        sa.column('provider_status', sa.String(length=100)),
        sa.column('public_checkout_token', sa.String(length=64)),
    )

    rows = bind.execute(
        sa.select(
            checkout_sessions.c.id,
            checkout_sessions.c.payment_intent_id,
            checkout_sessions.c.status,
        )
    ).fetchall()

    for row in rows:
        bind.execute(
            checkout_sessions.update()
            .where(checkout_sessions.c.id == row.id)
            .values(
                payment_provider='stripe',
                provider_status=row.status,
                public_checkout_token=uuid.uuid4().hex,
            )
        )

    op.alter_column(
        'checkout_sessions',
        'payment_intent_id',
        existing_type=sa.String(length=255),
        nullable=True,
    )
    op.alter_column(
        'checkout_sessions',
        'payment_provider',
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.alter_column(
        'checkout_sessions',
        'public_checkout_token',
        existing_type=sa.String(length=64),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        'checkout_sessions',
        'payment_intent_id',
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.drop_index(op.f('ix_checkout_sessions_public_checkout_token'), table_name='checkout_sessions')
    op.drop_index(op.f('ix_checkout_sessions_provider_capture_id'), table_name='checkout_sessions')
    op.drop_index(op.f('ix_checkout_sessions_provider_order_id'), table_name='checkout_sessions')
    op.drop_column('checkout_sessions', 'public_checkout_token')
    op.drop_column('checkout_sessions', 'provider_status')
    op.drop_column('checkout_sessions', 'provider_capture_id')
    op.drop_column('checkout_sessions', 'provider_order_id')
    op.drop_column('checkout_sessions', 'payment_provider')
