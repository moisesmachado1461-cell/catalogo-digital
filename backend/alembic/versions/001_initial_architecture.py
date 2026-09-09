from alembic import op
import sqlalchemy as sa
revision="001_initial_architecture"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("business_models", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("name",sa.String(80),nullable=False), sa.Column("code",sa.String(40),nullable=False,unique=True), sa.Column("description",sa.Text()), sa.Column("primary_action",sa.String(50),nullable=False), sa.Column("default_capabilities",sa.JSON(),nullable=False), sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()), sa.Column("sort_order",sa.Integer(),nullable=False,server_default="0"), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_business_models_code","business_models",["code"],unique=True)
    op.create_table("business_categories", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("name",sa.String(120),nullable=False), sa.Column("slug",sa.String(120),nullable=False,unique=True), sa.Column("description",sa.Text()), sa.Column("business_model_id",sa.Integer(),sa.ForeignKey("business_models.id",ondelete="RESTRICT"),nullable=False), sa.Column("default_capabilities",sa.JSON(),nullable=False), sa.Column("icon",sa.String(100)), sa.Column("image_url",sa.String(500)), sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()), sa.Column("sort_order",sa.Integer(),nullable=False,server_default="0"), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_business_categories_slug","business_categories",["slug"],unique=True)
    op.create_table("stores", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("name",sa.String(120),nullable=False), sa.Column("slug",sa.String(120),nullable=False,unique=True), sa.Column("business_category_id",sa.Integer(),sa.ForeignKey("business_categories.id",ondelete="RESTRICT"),nullable=False), sa.Column("business_model_id",sa.Integer(),sa.ForeignKey("business_models.id",ondelete="RESTRICT"),nullable=False), sa.Column("capabilities",sa.JSON(),nullable=False), sa.Column("description",sa.Text()), sa.Column("logo_url",sa.String(500)), sa.Column("banner_url",sa.String(500)), sa.Column("primary_color",sa.String(20),nullable=False), sa.Column("secondary_color",sa.String(20),nullable=False), sa.Column("whatsapp",sa.String(30)), sa.Column("phone",sa.String(30)), sa.Column("email",sa.String(255)), sa.Column("address",sa.String(255)), sa.Column("city",sa.String(120)), sa.Column("state",sa.String(2)), sa.Column("zip_code",sa.String(20)), sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_stores_slug","stores",["slug"],unique=True)
    op.create_index("ix_stores_business_category_id","stores",["business_category_id"])
    op.create_index("ix_stores_business_model_id","stores",["business_model_id"])
    op.create_table("users", sa.Column("id",sa.Integer(),primary_key=True), sa.Column("name",sa.String(120),nullable=False), sa.Column("email",sa.String(255),nullable=False,unique=True), sa.Column("password_hash",sa.String(255),nullable=False), sa.Column("role",sa.String(32),nullable=False), sa.Column("store_id",sa.Integer(),sa.ForeignKey("stores.id",ondelete="SET NULL")), sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()), sa.Column("email_verified",sa.Boolean(),nullable=False,server_default=sa.false()), sa.Column("last_login_at",sa.DateTime(timezone=True)), sa.Column("created_at",sa.DateTime(timezone=True),nullable=False), sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_users_email","users",["email"],unique=True)
    op.create_index("ix_users_role","users",["role"])
    op.create_index("ix_users_store_id","users",["store_id"])
def downgrade():
    for n,t in [("ix_users_store_id","users"),("ix_users_role","users"),("ix_users_email","users")]: op.drop_index(n,table_name=t)
    op.drop_table("users")
    for n in ["ix_stores_business_model_id","ix_stores_business_category_id","ix_stores_slug"]: op.drop_index(n,table_name="stores")
    op.drop_table("stores")
    op.drop_index("ix_business_categories_slug",table_name="business_categories"); op.drop_table("business_categories")
    op.drop_index("ix_business_models_code",table_name="business_models"); op.drop_table("business_models")
