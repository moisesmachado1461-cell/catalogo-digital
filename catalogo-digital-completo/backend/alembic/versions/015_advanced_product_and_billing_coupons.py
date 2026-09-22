"""advanced product and billing coupons

Revision ID: 015_advanced_coupons
Revises: 014_public_coupons
"""
from alembic import op
import sqlalchemy as sa

revision = "015_advanced_coupons"
down_revision = "014_public_coupons"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "coupon_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("coupon_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["coupon_id"], ["coupons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("coupon_id", "product_id", name="uq_coupon_product"),
    )
    op.create_index("ix_coupon_products_store_id", "coupon_products", ["store_id"])
    op.create_index("ix_coupon_products_coupon_id", "coupon_products", ["coupon_id"])
    op.create_index("ix_coupon_products_product_id", "coupon_products", ["product_id"])

    op.create_table(
        "billing_coupons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(length=16), nullable=False, server_default="PERCENT"),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("max_discount", sa.Numeric(12, 2), nullable=True),
        sa.Column("duration", sa.String(length=20), nullable=False, server_default="FIRST_INVOICE"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("value >= 0", name="ck_billing_coupons_value_nonnegative"),
        sa.CheckConstraint("max_discount IS NULL OR max_discount >= 0", name="ck_billing_coupons_max_discount_nonnegative"),
        sa.CheckConstraint("usage_limit IS NULL OR usage_limit >= 1", name="ck_billing_coupons_usage_limit_positive"),
        sa.CheckConstraint("usage_count >= 0", name="ck_billing_coupons_usage_count_nonnegative"),
        sa.UniqueConstraint("code", name="uq_billing_coupons_code"),
    )
    op.create_index("ix_billing_coupons_code", "billing_coupons", ["code"], unique=True)
    op.create_index("ix_billing_coupons_is_active", "billing_coupons", ["is_active"])

    op.create_table(
        "billing_coupon_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("coupon_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["coupon_id"], ["billing_coupons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("coupon_id", "plan_id", name="uq_billing_coupon_plan"),
    )
    op.create_index("ix_billing_coupon_plans_coupon_id", "billing_coupon_plans", ["coupon_id"])
    op.create_index("ix_billing_coupon_plans_plan_id", "billing_coupon_plans", ["plan_id"])

    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.add_column(sa.Column("billing_coupon_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_subscriptions_billing_coupon_id", "billing_coupons", ["billing_coupon_id"], ["id"], ondelete="SET NULL")
        batch_op.create_index("ix_subscriptions_billing_coupon_id", ["billing_coupon_id"], unique=False)

    with op.batch_alter_table("subscription_invoices") as batch_op:
        batch_op.add_column(sa.Column("subtotal_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("billing_coupon_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("coupon_code", sa.String(length=40), nullable=True))
        batch_op.create_foreign_key("fk_subscription_invoices_billing_coupon_id", "billing_coupons", ["billing_coupon_id"], ["id"], ondelete="SET NULL")
        batch_op.create_index("ix_subscription_invoices_billing_coupon_id", ["billing_coupon_id"], unique=False)
        batch_op.create_index("ix_subscription_invoices_coupon_code", ["coupon_code"], unique=False)

    op.execute("UPDATE subscription_invoices SET subtotal_amount = amount WHERE subtotal_amount = 0")

    op.create_table(
        "billing_coupon_usages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("coupon_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["coupon_id"], ["billing_coupons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invoice_id"], ["subscription_invoices.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("coupon_id", "invoice_id", name="uq_billing_coupon_usage_invoice"),
    )
    op.create_index("ix_billing_coupon_usages_coupon_id", "billing_coupon_usages", ["coupon_id"])
    op.create_index("ix_billing_coupon_usages_store_id", "billing_coupon_usages", ["store_id"])
    op.create_index("ix_billing_coupon_usages_subscription_id", "billing_coupon_usages", ["subscription_id"])
    op.create_index("ix_billing_coupon_usages_invoice_id", "billing_coupon_usages", ["invoice_id"])


def downgrade():
    op.drop_index("ix_billing_coupon_usages_invoice_id", table_name="billing_coupon_usages")
    op.drop_index("ix_billing_coupon_usages_subscription_id", table_name="billing_coupon_usages")
    op.drop_index("ix_billing_coupon_usages_store_id", table_name="billing_coupon_usages")
    op.drop_index("ix_billing_coupon_usages_coupon_id", table_name="billing_coupon_usages")
    op.drop_table("billing_coupon_usages")

    with op.batch_alter_table("subscription_invoices") as batch_op:
        batch_op.drop_index("ix_subscription_invoices_coupon_code")
        batch_op.drop_index("ix_subscription_invoices_billing_coupon_id")
        batch_op.drop_constraint("fk_subscription_invoices_billing_coupon_id", type_="foreignkey")
        batch_op.drop_column("coupon_code")
        batch_op.drop_column("billing_coupon_id")
        batch_op.drop_column("discount_amount")
        batch_op.drop_column("subtotal_amount")

    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_index("ix_subscriptions_billing_coupon_id")
        batch_op.drop_constraint("fk_subscriptions_billing_coupon_id", type_="foreignkey")
        batch_op.drop_column("billing_coupon_id")

    op.drop_index("ix_billing_coupon_plans_plan_id", table_name="billing_coupon_plans")
    op.drop_index("ix_billing_coupon_plans_coupon_id", table_name="billing_coupon_plans")
    op.drop_table("billing_coupon_plans")

    op.drop_index("ix_billing_coupons_is_active", table_name="billing_coupons")
    op.drop_index("ix_billing_coupons_code", table_name="billing_coupons")
    op.drop_table("billing_coupons")

    op.drop_index("ix_coupon_products_product_id", table_name="coupon_products")
    op.drop_index("ix_coupon_products_coupon_id", table_name="coupon_products")
    op.drop_index("ix_coupon_products_store_id", table_name="coupon_products")
    op.drop_table("coupon_products")
