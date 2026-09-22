"""reservations and rentals

Revision ID: 007_reservations_rentals
Revises: 006_booking_experience
"""
from alembic import op
import sqlalchemy as sa

revision = "007_reservations_rentals"
down_revision = "006_booking_experience"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("resource_type", sa.String(60), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("price_per_day", sa.Numeric(12,2), nullable=False),
        sa.Column("image_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "slug", name="uq_resources_store_slug"),
        sa.CheckConstraint("capacity > 0", name="ck_resources_capacity_positive"),
        sa.CheckConstraint("price_per_day >= 0", name="ck_resources_price_nonnegative"),
    )
    op.create_index("ix_resources_store_id", "resources", ["store_id"])
    op.create_index("ix_resources_is_active", "resources", ["is_active"])

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_token", sa.String(80), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("guests", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("daily_rate_snapshot", sa.Numeric(12,2), nullable=False),
        sa.Column("total", sa.Numeric(12,2), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("public_token"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_reservations_time_order"),
        sa.CheckConstraint("guests > 0", name="ck_reservations_guests_positive"),
        sa.CheckConstraint("total >= 0", name="ck_reservations_total_nonnegative"),
    )
    for col in ["public_token","store_id","customer_id","resource_id","starts_at","ends_at","status"]:
        op.create_index(f"ix_reservations_{col}", "reservations", [col], unique=(col=="public_token"))

    op.create_table(
        "rental_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("sku", sa.String(80)),
        sa.Column("daily_rate", sa.Numeric(12,2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(12,2), nullable=False),
        sa.Column("quantity_total", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "slug", name="uq_rental_items_store_slug"),
        sa.UniqueConstraint("store_id", "sku", name="uq_rental_items_store_sku"),
        sa.CheckConstraint("daily_rate >= 0", name="ck_rental_items_rate_nonnegative"),
        sa.CheckConstraint("deposit_amount >= 0", name="ck_rental_items_deposit_nonnegative"),
        sa.CheckConstraint("quantity_total > 0", name="ck_rental_items_quantity_positive"),
    )
    op.create_index("ix_rental_items_store_id", "rental_items", ["store_id"])
    op.create_index("ix_rental_items_is_active", "rental_items", ["is_active"])

    op.create_table(
        "rental_reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_token", sa.String(80), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("rental_item_id", sa.Integer(), sa.ForeignKey("rental_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("rental_days", sa.Integer(), nullable=False),
        sa.Column("daily_rate_snapshot", sa.Numeric(12,2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(12,2), nullable=False),
        sa.Column("total", sa.Numeric(12,2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("public_token"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_rental_reservations_time_order"),
        sa.CheckConstraint("quantity > 0", name="ck_rental_reservations_quantity_positive"),
        sa.CheckConstraint("rental_days > 0", name="ck_rental_reservations_days_positive"),
        sa.CheckConstraint("daily_rate_snapshot >= 0", name="ck_rental_reservations_rate_nonnegative"),
        sa.CheckConstraint("deposit_amount >= 0", name="ck_rental_reservations_deposit_nonnegative"),
        sa.CheckConstraint("total >= 0", name="ck_rental_reservations_total_nonnegative"),
    )
    for col in ["public_token","store_id","customer_id","rental_item_id","starts_at","ends_at","status"]:
        op.create_index(f"ix_rental_reservations_{col}", "rental_reservations", [col], unique=(col=="public_token"))


def downgrade():
    op.drop_table("rental_reservations")
    op.drop_table("rental_items")
    op.drop_table("reservations")
    op.drop_table("resources")
