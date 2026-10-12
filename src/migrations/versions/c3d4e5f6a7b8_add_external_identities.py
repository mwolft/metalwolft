"""Allow passwordless customer accounts with a linked external identity.

Revision ID: c3d4e5f6a7b8
Revises: c2d3e4f5a6b7
"""

from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "password", existing_type=sa.String(120), nullable=True)
    op.create_table(
        "external_identities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_external_identity_provider_subject"),
        sa.UniqueConstraint("user_id", "provider", name="uq_external_identity_user_provider"),
    )
    op.create_index("ix_external_identities_user_id", "external_identities", ["user_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT 1 FROM users WHERE password IS NULL LIMIT 1")).first():
        raise RuntimeError("No se puede revertir: existen cuentas sin contraseña local.")
    op.drop_index("ix_external_identities_user_id", table_name="external_identities")
    op.drop_table("external_identities")
    op.alter_column("users", "password", existing_type=sa.String(120), nullable=False)
