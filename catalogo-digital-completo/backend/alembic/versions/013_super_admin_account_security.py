"""super admin account security

Revision ID: 013_super_admin_account_security
Revises: 012_billing_engine
"""
from alembic import op
import sqlalchemy as sa

revision = "013_super_admin_account_security"
down_revision = "012_billing_engine"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("token_version", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("token_version")
