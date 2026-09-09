from alembic import op
import sqlalchemy as sa

revision = "002_catalog_sales"
down_revision = "001_initial_architecture"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("image_url", sa.String(500)),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "slug", name="uq_categories_store_slug"),
    )
    op.create_index("ix_categories_store_id", "categories", ["store_id"])

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("sku", sa.String(80)),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("compare_at_price", sa.Numeric(12, 2)),
        sa.Column("image_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("track_inventory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "slug", name="uq_products_store_slug"),
        sa.UniqueConstraint("store_id", "sku", name="uq_products_store_sku"),
        sa.CheckConstraint("price >= 0", name="ck_products_price_nonnegative"),
        sa.CheckConstraint("compare_at_price IS NULL OR compare_at_price >= 0", name="ck_products_compare_price_nonnegative"),
    )
    op.create_index("ix_products_store_id", "products", ["store_id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_is_active", "products", ["is_active"])

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("sku", sa.String(80)),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "sku", name="uq_product_variants_store_sku"),
        sa.CheckConstraint("price IS NULL OR price >= 0", name="ck_product_variants_price_nonnegative"),
    )
    op.create_index("ix_product_variants_store_id", "product_variants", ["store_id"])
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])

    op.create_table(
        "product_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("min_selections", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_selections", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("min_selections >= 0", name="ck_product_options_min_nonnegative"),
        sa.CheckConstraint("max_selections >= 1", name="ck_product_options_max_positive"),
        sa.CheckConstraint("max_selections >= min_selections", name="ck_product_options_max_gte_min"),
    )
    op.create_index("ix_product_options_store_id", "product_options", ["store_id"])
    op.create_index("ix_product_options_product_id", "product_options", ["product_id"])

    op.create_table(
        "product_option_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_option_id", sa.Integer(), sa.ForeignKey("product_options.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("price_adjustment", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price_adjustment >= 0", name="ck_product_option_items_price_nonnegative"),
    )
    op.create_index("ix_product_option_items_store_id", "product_option_items", ["store_id"])
    op.create_index("ix_product_option_items_product_option_id", "product_option_items", ["product_option_id"])

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(30)),
        sa.Column("address", sa.String(255)),
        sa.Column("city", sa.String(120)),
        sa.Column("state", sa.String(2)),
        sa.Column("zip_code", sa.String(20)),
        sa.Column("notes", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_customers_store_id", "customers", ["store_id"])
    op.create_index("ix_customers_user_id", "customers", ["user_id"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_phone", "customers", ["phone"])

    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT")),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "product_id", "variant_id", name="uq_inventory_store_product_variant"),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonnegative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"),
        sa.CheckConstraint("min_quantity >= 0", name="ck_inventory_min_nonnegative"),
    )
    op.create_index("ix_inventory_store_id", "inventory", ["store_id"])
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"])
    op.create_index("ix_inventory_variant_id", "inventory", ["variant_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("order_number", sa.String(40), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDENTE"),
        sa.Column("payment_method", sa.String(32), nullable=False),
        sa.Column("fulfillment_method", sa.String(32), nullable=False, server_default="RETIRADA"),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("delivery_fee", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text()),
        sa.Column("delivery_address", sa.String(255)),
        sa.Column("delivery_city", sa.String(120)),
        sa.Column("delivery_state", sa.String(2)),
        sa.Column("delivery_zip_code", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "order_number", name="uq_orders_store_number"),
        sa.CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_nonnegative"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_orders_discount_nonnegative"),
        sa.CheckConstraint("delivery_fee >= 0", name="ck_orders_delivery_fee_nonnegative"),
        sa.CheckConstraint("total >= 0", name="ck_orders_total_nonnegative"),
    )
    op.create_index("ix_orders_store_id", "orders", ["store_id"])
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="SET NULL")),
        sa.Column("product_name", sa.String(160), nullable=False),
        sa.Column("variant_name", sa.String(120)),
        sa.Column("sku", sa.String(80)),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_nonnegative"),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("line_total >= 0", name="ck_order_items_line_total_nonnegative"),
    )
    op.create_index("ix_order_items_store_id", "order_items", ["store_id"])
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
    op.create_index("ix_order_items_variant_id", "order_items", ["variant_id"])


def downgrade():
    for index in ["ix_order_items_variant_id", "ix_order_items_product_id", "ix_order_items_order_id", "ix_order_items_store_id"]:
        op.drop_index(index, table_name="order_items")
    op.drop_table("order_items")
    for index in ["ix_orders_created_at", "ix_orders_status", "ix_orders_customer_id", "ix_orders_store_id"]:
        op.drop_index(index, table_name="orders")
    op.drop_table("orders")
    for index in ["ix_inventory_variant_id", "ix_inventory_product_id", "ix_inventory_store_id"]:
        op.drop_index(index, table_name="inventory")
    op.drop_table("inventory")
    for index in ["ix_customers_phone", "ix_customers_email", "ix_customers_user_id", "ix_customers_store_id"]:
        op.drop_index(index, table_name="customers")
    op.drop_table("customers")
    for index in ["ix_product_option_items_product_option_id", "ix_product_option_items_store_id"]:
        op.drop_index(index, table_name="product_option_items")
    op.drop_table("product_option_items")
    for index in ["ix_product_options_product_id", "ix_product_options_store_id"]:
        op.drop_index(index, table_name="product_options")
    op.drop_table("product_options")
    for index in ["ix_product_variants_product_id", "ix_product_variants_store_id"]:
        op.drop_index(index, table_name="product_variants")
    op.drop_table("product_variants")
    for index in ["ix_products_is_active", "ix_products_category_id", "ix_products_store_id"]:
        op.drop_index(index, table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_store_id", table_name="categories")
    op.drop_table("categories")
