"""add verifactu ready fields

Revision ID: c5d6e7f8a9b0
Revises: b3c4d5e6f7a8
Create Date: 2026-07-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'c5d6e7f8a9b0'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('verifactu_records', sa.Column('official_payload', sa.JSON(), nullable=True))
    op.add_column('verifactu_records', sa.Column('official_payload_schema_version', sa.Integer(), nullable=True))
    op.add_column('verifactu_records', sa.Column('fingerprint_input', sa.Text(), nullable=True))
    op.add_column('verifactu_records', sa.Column('fingerprint_calculated_at', sa.DateTime(), nullable=True))
    op.add_column('verifactu_records', sa.Column('previous_record_id', sa.Integer(), nullable=True))
    op.add_column('verifactu_records', sa.Column('previous_fingerprint', sa.String(length=128), nullable=True))
    op.add_column('verifactu_records', sa.Column('is_first_record', sa.Boolean(), nullable=True))
    op.add_column('verifactu_records', sa.Column('installation_id', sa.String(length=100), nullable=True))
    op.add_column('verifactu_records', sa.Column('producer_name', sa.String(length=120), nullable=True))
    op.add_column('verifactu_records', sa.Column('producer_tax_id', sa.String(length=50), nullable=True))
    op.add_column('verifactu_records', sa.Column('generation_timestamp', sa.DateTime(), nullable=True))
    op.add_column('verifactu_records', sa.Column('generation_timezone', sa.String(length=50), nullable=True))
    op.add_column('verifactu_records', sa.Column('ready_at', sa.DateTime(), nullable=True))
    op.create_unique_constraint(
        'uq_verifactu_records_fingerprint',
        'verifactu_records',
        ['fingerprint'],
    )
    op.create_foreign_key(
        'fk_verifactu_records_previous_record_id',
        'verifactu_records',
        'verifactu_records',
        ['previous_record_id'],
        ['id'],
    )
    op.create_check_constraint(
        'ck_verifactu_records_previous_not_self',
        'verifactu_records',
        'previous_record_id IS NULL OR previous_record_id != id',
    )
    op.create_index(
        'ix_verifactu_records_previous_record_id',
        'verifactu_records',
        ['previous_record_id'],
        unique=True,
    )


def downgrade():
    op.drop_index('ix_verifactu_records_previous_record_id', table_name='verifactu_records')
    op.drop_constraint('ck_verifactu_records_previous_not_self', 'verifactu_records', type_='check')
    op.drop_constraint('fk_verifactu_records_previous_record_id', 'verifactu_records', type_='foreignkey')
    op.drop_constraint('uq_verifactu_records_fingerprint', 'verifactu_records', type_='unique')
    op.drop_column('verifactu_records', 'ready_at')
    op.drop_column('verifactu_records', 'generation_timezone')
    op.drop_column('verifactu_records', 'generation_timestamp')
    op.drop_column('verifactu_records', 'producer_tax_id')
    op.drop_column('verifactu_records', 'producer_name')
    op.drop_column('verifactu_records', 'installation_id')
    op.drop_column('verifactu_records', 'is_first_record')
    op.drop_column('verifactu_records', 'previous_fingerprint')
    op.drop_column('verifactu_records', 'previous_record_id')
    op.drop_column('verifactu_records', 'fingerprint_calculated_at')
    op.drop_column('verifactu_records', 'fingerprint_input')
    op.drop_column('verifactu_records', 'official_payload_schema_version')
    op.drop_column('verifactu_records', 'official_payload')
