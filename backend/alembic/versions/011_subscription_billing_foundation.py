"""subscription billing multi gateway foundation

Revision ID: 011_subscription_billing
Revises: 010_security_lgpd
"""
from alembic import op
import sqlalchemy as sa

revision = "011_subscription_billing"
down_revision = "010_security_lgpd"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.add_column(sa.Column("provider_status", sa.String(60), nullable=True))
        batch_op.add_column(sa.Column("external_plan_id", sa.String(160), nullable=True))
        batch_op.add_column(sa.Column("external_price_id", sa.String(160), nullable=True))
        batch_op.add_column(sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("next_billing_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index("ix_subscriptions_next_billing_at", ["next_billing_at"], unique=False)

    op.create_table(
        "billing_gateway_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("billing_cycle", sa.String(16), nullable=False, server_default="MONTHLY"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("external_plan_id", sa.String(160), nullable=True),
        sa.Column("external_price_id", sa.String(160), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "plan_id",
            "provider",
            "billing_cycle",
            "currency",
            name="uq_billing_gateway_price_plan_provider_cycle_currency",
        ),
    )
    for col in ["plan_id", "provider", "billing_cycle", "external_plan_id", "external_price_id", "is_active"]:
        op.create_index(f"ix_billing_gateway_prices_{col}", "billing_gateway_prices", [col])

    op.create_table(
        "subscription_invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("external_invoice_id", sa.String(160), nullable=True),
        sa.Column("external_payment_id", sa.String(160), nullable=True),
        sa.Column("payment_method", sa.String(40), nullable=True),
        sa.Column("checkout_url", sa.String(700), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "provider",
            "external_invoice_id",
            name="uq_subscription_invoice_provider_external_invoice",
        ),
    )
    for col in [
        "store_id",
        "subscription_id",
        "provider",
        "status",
        "external_invoice_id",
        "external_payment_id",
        "due_at",
        "paid_at",
    ]:
        op.create_index(f"ix_subscription_invoices_{col}", "subscription_invoices", [col])

    op.create_table(
        "billing_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("external_event_id", sa.String(190), nullable=True),
        sa.Column("event_type", sa.String(120), nullable=True),
        sa.Column("resource_id", sa.String(190), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="RECEIVED"),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "provider",
            "external_event_id",
            name="uq_billing_webhook_provider_external_event",
        ),
    )
    for col in ["provider", "external_event_id", "event_type", "resource_id", "status", "payload_hash", "received_at"]:
        op.create_index(f"ix_billing_webhook_events_{col}", "billing_webhook_events", [col])


def downgrade():
    op.drop_table("billing_webhook_events")
    op.drop_table("subscription_invoices")
    op.drop_table("billing_gateway_prices")

    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_index("ix_subscriptions_next_billing_at")
        batch_op.drop_column("next_billing_at")
        batch_op.drop_column("cancel_at_period_end")
        batch_op.drop_column("auto_renew")
        batch_op.drop_column("external_price_id")
        batch_op.drop_column("external_plan_id")
        batch_op.drop_column("provider_status")
