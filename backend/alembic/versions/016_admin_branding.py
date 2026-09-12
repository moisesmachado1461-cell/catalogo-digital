"""admin panel branding

Revision ID: 016_admin_branding
Revises: 015_advanced_coupons
"""
from alembic import op
import sqlalchemy as sa

revision = "016_admin_branding"
down_revision = "015_advanced_coupons"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("stores") as batch_op:
        batch_op.add_column(sa.Column("panel_brand_name", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("panel_logo_url", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("stores") as batch_op:
        batch_op.drop_column("panel_logo_url")
        batch_op.drop_column("panel_brand_name")
