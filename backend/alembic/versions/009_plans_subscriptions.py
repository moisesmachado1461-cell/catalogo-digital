"""plans and subscriptions

Revision ID: 009_plans_subscriptions
Revises: 008_payments
"""
from alembic import op
import sqlalchemy as sa

revision = "009_plans_subscriptions"
down_revision = "008_payments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("monthly_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("yearly_price", sa.Numeric(12, 2)),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_plans_code"),
    )
    op.create_index("ix_plans_code", "plans", ["code"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
        sa.Column("billing_cycle", sa.String(16), nullable=False, server_default="MONTHLY"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True)),
        sa.Column("canceled_at", sa.DateTime(timezone=True)),
        sa.Column("provider", sa.String(40), nullable=False, server_default="MANUAL"),
        sa.Column("external_customer_id", sa.String(160)),
        sa.Column("external_subscription_id", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for col in ["store_id", "plan_id", "status", "current_period_end", "external_customer_id", "external_subscription_id"]:
        op.create_index(f"ix_subscriptions_{col}", "subscriptions", [col])


def downgrade():
    op.drop_table("subscriptions")
    op.drop_table("plans")
