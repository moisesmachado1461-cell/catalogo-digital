"""marketing, coupons, promotions and richer checkout

Revision ID: 005_marketing_checkout
Revises: 004_quotes
"""
from alembic import op
import sqlalchemy as sa

revision = "005_marketing_checkout"
down_revision = "004_quotes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("discount_type", sa.String(16), nullable=False, server_default="PERCENT"),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("min_order_value", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("max_discount", sa.Numeric(12, 2)),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("usage_limit", sa.Integer()),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "code", name="uq_coupons_store_code"),
        sa.CheckConstraint("value >= 0", name="ck_coupons_value_nonnegative"),
        sa.CheckConstraint("min_order_value >= 0", name="ck_coupons_min_order_nonnegative"),
        sa.CheckConstraint("max_discount IS NULL OR max_discount >= 0", name="ck_coupons_max_discount_nonnegative"),
        sa.CheckConstraint("usage_limit IS NULL OR usage_limit >= 1", name="ck_coupons_usage_limit_positive"),
        sa.CheckConstraint("usage_count >= 0", name="ck_coupons_usage_count_nonnegative"),
    )
    op.create_index("ix_coupons_store_id", "coupons", ["store_id"])
    op.create_index("ix_coupons_is_active", "coupons", ["is_active"])

    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("discount_type", sa.String(16), nullable=False, server_default="PERCENT"),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("value >= 0", name="ck_promotions_value_nonnegative"),
    )
    op.create_index("ix_promotions_store_id", "promotions", ["store_id"])
    op.create_index("ix_promotions_is_active", "promotions", ["is_active"])

    op.create_table(
        "promotion_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("promotion_id", sa.Integer(), sa.ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("promotion_id", "product_id", name="uq_promotion_product"),
    )
    op.create_index("ix_promotion_items_store_id", "promotion_items", ["store_id"])
    op.create_index("ix_promotion_items_promotion_id", "promotion_items", ["promotion_id"])
    op.create_index("ix_promotion_items_product_id", "promotion_items", ["product_id"])

    op.create_table(
        "coupon_usages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("coupon_id", sa.Integer(), sa.ForeignKey("coupons.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("coupon_id", "order_id", name="uq_coupon_usage_order"),
    )
    op.create_index("ix_coupon_usages_store_id", "coupon_usages", ["store_id"])
    op.create_index("ix_coupon_usages_coupon_id", "coupon_usages", ["coupon_id"])
    op.create_index("ix_coupon_usages_order_id", "coupon_usages", ["order_id"])
    op.create_index("ix_coupon_usages_customer_id", "coupon_usages", ["customer_id"])

    op.add_column("orders", sa.Column("coupon_code", sa.String(40)))
    op.add_column("order_items", sa.Column("original_unit_price", sa.Numeric(12, 2)))
    op.add_column("order_items", sa.Column("promotion_name", sa.String(120)))
    op.add_column("order_items", sa.Column("selected_options", sa.JSON()))


def downgrade():
    op.drop_column("order_items", "selected_options")
    op.drop_column("order_items", "promotion_name")
    op.drop_column("order_items", "original_unit_price")
    op.drop_column("orders", "coupon_code")
    op.drop_table("coupon_usages")
    op.drop_table("promotion_items")
    op.drop_table("promotions")
    op.drop_table("coupons")
