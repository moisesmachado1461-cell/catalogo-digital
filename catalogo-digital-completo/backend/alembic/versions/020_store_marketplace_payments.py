"""store marketplace payments via Mercado Pago OAuth

Revision ID: 020_store_marketplace_payments
Revises: 019_dynamic_plans_pix
"""

from alembic import op
import sqlalchemy as sa

revision = "020_store_marketplace_payments"
down_revision = "019_dynamic_plans_pix"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("payments", sa.Column("provider_status", sa.String(length=120), nullable=True))
    op.add_column("payments", sa.Column("provider_idempotency_key", sa.String(length=80), nullable=True))
    op.add_column("payments", sa.Column("pix_qr_code", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("pix_qr_code_base64", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("pix_ticket_url", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("pix_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_payments_provider_idempotency_key",
        "payments",
        ["provider_idempotency_key"],
        unique=True,
    )

    op.create_table(
        "store_payment_gateway_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="MERCADO_PAGO"),
        sa.Column("external_user_id", sa.String(length=120), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CONNECTED"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "provider", name="uq_store_payment_gateway_account"),
    )
    op.create_index("ix_store_payment_gateway_accounts_store_id", "store_payment_gateway_accounts", ["store_id"])
    op.create_index("ix_store_payment_gateway_accounts_provider", "store_payment_gateway_accounts", ["provider"])
    op.create_index("ix_store_payment_gateway_accounts_external_user_id", "store_payment_gateway_accounts", ["external_user_id"])
    op.create_index("ix_store_payment_gateway_accounts_status", "store_payment_gateway_accounts", ["status"])

    op.create_table(
        "store_payment_oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="MERCADO_PAGO"),
        sa.Column("state_digest", sa.String(length=64), nullable=False),
        sa.Column("code_verifier_encrypted", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("state_digest", name="uq_store_payment_oauth_state_digest"),
    )
    op.create_index("ix_store_payment_oauth_states_store_id", "store_payment_oauth_states", ["store_id"])
    op.create_index("ix_store_payment_oauth_states_provider", "store_payment_oauth_states", ["provider"])
    op.create_index("ix_store_payment_oauth_states_state_digest", "store_payment_oauth_states", ["state_digest"], unique=True)
    op.create_index("ix_store_payment_oauth_states_expires_at", "store_payment_oauth_states", ["expires_at"])


def downgrade():
    op.drop_index("ix_store_payment_oauth_states_expires_at", table_name="store_payment_oauth_states")
    op.drop_index("ix_store_payment_oauth_states_state_digest", table_name="store_payment_oauth_states")
    op.drop_index("ix_store_payment_oauth_states_provider", table_name="store_payment_oauth_states")
    op.drop_index("ix_store_payment_oauth_states_store_id", table_name="store_payment_oauth_states")
    op.drop_table("store_payment_oauth_states")

    op.drop_index("ix_store_payment_gateway_accounts_status", table_name="store_payment_gateway_accounts")
    op.drop_index("ix_store_payment_gateway_accounts_external_user_id", table_name="store_payment_gateway_accounts")
    op.drop_index("ix_store_payment_gateway_accounts_provider", table_name="store_payment_gateway_accounts")
    op.drop_index("ix_store_payment_gateway_accounts_store_id", table_name="store_payment_gateway_accounts")
    op.drop_table("store_payment_gateway_accounts")

    op.drop_index("ix_payments_provider_idempotency_key", table_name="payments")
    op.drop_column("payments", "pix_expires_at")
    op.drop_column("payments", "pix_ticket_url")
    op.drop_column("payments", "pix_qr_code_base64")
    op.drop_column("payments", "pix_qr_code")
    op.drop_column("payments", "provider_idempotency_key")
    op.drop_column("payments", "provider_status")
