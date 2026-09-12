"""public coupons storefront

Revision ID: 014_public_coupons
Revises: 013_super_admin_account_security
"""
from alembic import op
import sqlalchemy as sa

revision = "014_public_coupons"
down_revision = "013_super_admin_account_security"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("coupons") as batch_op:
        batch_op.add_column(
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.create_index("ix_coupons_is_public", ["is_public"], unique=False)


def downgrade():
    with op.batch_alter_table("coupons") as batch_op:
        batch_op.drop_index("ix_coupons_is_public")
        batch_op.drop_column("is_public")
