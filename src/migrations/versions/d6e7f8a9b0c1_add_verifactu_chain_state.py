"""add verifactu chain state

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd6e7f8a9b0c1'
down_revision = 'c5d6e7f8a9b0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('verifactu_records', sa.Column('chain_key', sa.String(length=300), nullable=True))
    op.add_column('verifactu_records', sa.Column('chain_sequence', sa.Integer(), nullable=True))
    op.create_unique_constraint(
        'uq_verifactu_records_chain_sequence',
        'verifactu_records',
        ['chain_key', 'chain_sequence'],
    )
    op.create_check_constraint(
        'ck_verifactu_records_chain_sequence_positive',
        'verifactu_records',
        'chain_sequence IS NULL OR chain_sequence >= 1',
    )
    op.create_check_constraint(
        'ck_verifactu_records_ready_chain_complete',
        'verifactu_records',
        "status != 'READY' OR (chain_key IS NOT NULL AND chain_sequence IS NOT NULL AND fingerprint IS NOT NULL)",
    )
    op.create_check_constraint(
        'ck_verifactu_records_first_previous_coherent',
        'verifactu_records',
        "is_first_record IS NULL OR "
        "(is_first_record = true AND previous_record_id IS NULL AND chain_sequence = 1) OR "
        "(is_first_record = false AND previous_record_id IS NOT NULL AND chain_sequence > 1)",
    )
    op.create_index(
        'ix_verifactu_records_chain_key_sequence',
        'verifactu_records',
        ['chain_key', 'chain_sequence'],
        unique=False,
    )

    op.create_table(
        'verifactu_chain_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chain_key', sa.String(length=300), nullable=False),
        sa.Column('issuer_tax_id', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('mode', sa.String(length=30), nullable=False),
        sa.Column('system_id', sa.String(length=100), nullable=False),
        sa.Column('installation_id', sa.String(length=100), nullable=False),
        sa.Column('producer_tax_id', sa.String(length=50), nullable=False),
        sa.Column('last_record_id', sa.Integer(), nullable=True),
        sa.Column('last_fingerprint', sa.String(length=128), nullable=True),
        sa.Column('next_sequence', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['last_record_id'], ['verifactu_records.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chain_key', name='uq_verifactu_chain_states_chain_key'),
    )
    op.create_index(
        'ix_verifactu_chain_states_chain_key',
        'verifactu_chain_states',
        ['chain_key'],
        unique=False,
    )


def downgrade():
    op.drop_index('ix_verifactu_chain_states_chain_key', table_name='verifactu_chain_states')
    op.drop_table('verifactu_chain_states')
    op.drop_index('ix_verifactu_records_chain_key_sequence', table_name='verifactu_records')
    op.drop_constraint('ck_verifactu_records_first_previous_coherent', 'verifactu_records', type_='check')
    op.drop_constraint('ck_verifactu_records_ready_chain_complete', 'verifactu_records', type_='check')
    op.drop_constraint('ck_verifactu_records_chain_sequence_positive', 'verifactu_records', type_='check')
    op.drop_constraint('uq_verifactu_records_chain_sequence', 'verifactu_records', type_='unique')
    op.drop_column('verifactu_records', 'chain_sequence')
    op.drop_column('verifactu_records', 'chain_key')
