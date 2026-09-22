"""payments and payment settings

Revision ID: 008_payments
Revises: 007_reservations_rentals
"""
from alembic import op
import sqlalchemy as sa

revision = "008_payments"
down_revision = "007_reservations_rentals"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payment_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pix_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pix_key_type", sa.String(20)),
        sa.Column("pix_key", sa.String(255)),
        sa.Column("pix_receiver_name", sa.String(160)),
        sa.Column("pix_receiver_city", sa.String(120)),
        sa.Column("cash_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("card_on_delivery_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("whatsapp_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("online_gateway", sa.String(40), nullable=False, server_default="NONE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", name="uq_payment_settings_store"),
    )
    op.create_index("ix_payment_settings_store_id", "payment_settings", ["store_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_token", sa.String(80), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reference_type", sa.String(24), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False, server_default="MANUAL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDENTE"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("pix_key_type_snapshot", sa.String(20)),
        sa.Column("pix_key_snapshot", sa.String(255)),
        sa.Column("pix_receiver_name_snapshot", sa.String(160)),
        sa.Column("pix_receiver_city_snapshot", sa.String(120)),
        sa.Column("instructions", sa.Text()),
        sa.Column("external_id", sa.String(160)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("public_token"),
        sa.UniqueConstraint("store_id", "reference_type", "reference_id", name="uq_payments_store_reference"),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
    )
    op.create_index("ix_payments_public_token", "payments", ["public_token"], unique=True)
    for col in ["store_id", "reference_type", "reference_id", "method", "status", "external_id", "created_at"]:
        op.create_index(f"ix_payments_{col}", "payments", [col])


def downgrade():
    op.drop_table("payments")
    op.drop_table("payment_settings")
