"""billing lifecycle engine

Revision ID: 012_billing_engine
Revises: 011_subscription_billing
"""
from alembic import op
import sqlalchemy as sa

revision = "012_billing_engine"
down_revision = "011_subscription_billing"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("subscription_invoices") as batch_op:
        batch_op.add_column(sa.Column("plan_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("invoice_type", sa.String(24), nullable=False, server_default="RENEWAL"))
        batch_op.add_column(sa.Column("billing_cycle", sa.String(16), nullable=False, server_default="MONTHLY"))
        batch_op.add_column(sa.Column("period_start", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("period_end", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key(
            "fk_subscription_invoices_plan_id_plans",
            "plans",
            ["plan_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index("ix_subscription_invoices_plan_id", ["plan_id"], unique=False)
        batch_op.create_index("ix_subscription_invoices_invoice_type", ["invoice_type"], unique=False)
        batch_op.create_index("ix_subscription_invoices_period_start", ["period_start"], unique=False)
        batch_op.create_index("ix_subscription_invoices_period_end", ["period_end"], unique=False)

    # Compatibilidade com faturas eventualmente criadas pela Fase 19.1.
    op.execute(
        sa.text(
            """
            UPDATE subscription_invoices
            SET plan_id = (
                SELECT subscriptions.plan_id
                FROM subscriptions
                WHERE subscriptions.id = subscription_invoices.subscription_id
            )
            WHERE plan_id IS NULL AND subscription_id IS NOT NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE subscription_invoices
            SET billing_cycle = COALESCE((
                SELECT subscriptions.billing_cycle
                FROM subscriptions
                WHERE subscriptions.id = subscription_invoices.subscription_id
            ), 'MONTHLY')
            """
        )
    )


def downgrade():
    with op.batch_alter_table("subscription_invoices") as batch_op:
        batch_op.drop_index("ix_subscription_invoices_period_end")
        batch_op.drop_index("ix_subscription_invoices_period_start")
        batch_op.drop_index("ix_subscription_invoices_invoice_type")
        batch_op.drop_index("ix_subscription_invoices_plan_id")
        batch_op.drop_constraint("fk_subscription_invoices_plan_id_plans", type_="foreignkey")
        batch_op.drop_column("last_attempt_at")
        batch_op.drop_column("attempt_count")
        batch_op.drop_column("period_end")
        batch_op.drop_column("period_start")
        batch_op.drop_column("billing_cycle")
        batch_op.drop_column("invoice_type")
        batch_op.drop_column("plan_id")
