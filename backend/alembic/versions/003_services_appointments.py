from alembic import op
import sqlalchemy as sa

revision = "003_services_appointments"
down_revision = "002_catalog_sales"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "slug", name="uq_services_store_slug"),
        sa.CheckConstraint("price >= 0", name="ck_services_price_nonnegative"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_services_duration_positive"),
    )
    op.create_index("ix_services_store_id", "services", ["store_id"])
    op.create_index("ix_services_category_id", "services", ["category_id"])
    op.create_index("ix_services_is_active", "services", ["is_active"])

    op.create_table(
        "professionals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("phone", sa.String(30)),
        sa.Column("email", sa.String(255)),
        sa.Column("image_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_professionals_store_id", "professionals", ["store_id"])
    op.create_index("ix_professionals_is_active", "professionals", ["is_active"])

    op.create_table(
        "professional_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("professional_id", sa.Integer(), sa.ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("professional_id", "service_id", name="uq_professional_services_pair"),
    )
    op.create_index("ix_professional_services_store_id", "professional_services", ["store_id"])
    op.create_index("ix_professional_services_professional_id", "professional_services", ["professional_id"])
    op.create_index("ix_professional_services_service_id", "professional_services", ["service_id"])

    op.create_table(
        "professional_hours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("professional_id", sa.Integer(), sa.ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("professional_id", "day_of_week", name="uq_professional_hours_day"),
        sa.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_professional_hours_day"),
        sa.CheckConstraint("start_time < end_time", name="ck_professional_hours_order"),
    )
    op.create_index("ix_professional_hours_store_id", "professional_hours", ["store_id"])
    op.create_index("ix_professional_hours_professional_id", "professional_hours", ["professional_id"])
    op.create_index("ix_professional_hours_day_of_week", "professional_hours", ["day_of_week"])

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("professional_id", sa.Integer(), sa.ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDENTE"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="ck_appointments_time_order"),
    )
    op.create_index("ix_appointments_store_id", "appointments", ["store_id"])
    op.create_index("ix_appointments_customer_id", "appointments", ["customer_id"])
    op.create_index("ix_appointments_service_id", "appointments", ["service_id"])
    op.create_index("ix_appointments_professional_id", "appointments", ["professional_id"])
    op.create_index("ix_appointments_starts_at", "appointments", ["starts_at"])
    op.create_index("ix_appointments_status", "appointments", ["status"])


def downgrade():
    for index in [
        "ix_appointments_status",
        "ix_appointments_starts_at",
        "ix_appointments_professional_id",
        "ix_appointments_service_id",
        "ix_appointments_customer_id",
        "ix_appointments_store_id",
    ]:
        op.drop_index(index, table_name="appointments")
    op.drop_table("appointments")

    for index in [
        "ix_professional_hours_day_of_week",
        "ix_professional_hours_professional_id",
        "ix_professional_hours_store_id",
    ]:
        op.drop_index(index, table_name="professional_hours")
    op.drop_table("professional_hours")

    for index in [
        "ix_professional_services_service_id",
        "ix_professional_services_professional_id",
        "ix_professional_services_store_id",
    ]:
        op.drop_index(index, table_name="professional_services")
    op.drop_table("professional_services")

    for index in ["ix_professionals_is_active", "ix_professionals_store_id"]:
        op.drop_index(index, table_name="professionals")
    op.drop_table("professionals")

    for index in ["ix_services_is_active", "ix_services_category_id", "ix_services_store_id"]:
        op.drop_index(index, table_name="services")
    op.drop_table("services")
