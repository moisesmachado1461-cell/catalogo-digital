"""customer portal and order tracking

Revision ID: 017_customer_portal
Revises: 016_admin_branding
"""
from alembic import op
import sqlalchemy as sa
import secrets

revision = "017_customer_portal"
down_revision = "016_admin_branding"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("public_token", sa.String(length=80), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM orders WHERE public_token IS NULL")).fetchall()
    for row in rows:
        connection.execute(
            sa.text("UPDATE orders SET public_token = :token WHERE id = :id"),
            {"token": secrets.token_urlsafe(18), "id": row[0]},
        )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column("public_token", existing_type=sa.String(length=80), nullable=False)
        batch_op.create_unique_constraint("uq_orders_public_token", ["public_token"])
        batch_op.create_index("ix_orders_public_token", ["public_token"], unique=True)

    op.create_table(
        "customer_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("store_id", "email", name="uq_customer_accounts_store_email"),
        sa.UniqueConstraint("store_id", "customer_id", name="uq_customer_accounts_store_customer"),
    )
    op.create_index("ix_customer_accounts_store_id", "customer_accounts", ["store_id"], unique=False)
    op.create_index("ix_customer_accounts_customer_id", "customer_accounts", ["customer_id"], unique=False)
    op.create_index("ix_customer_accounts_email", "customer_accounts", ["email"], unique=False)


def downgrade():
    op.drop_index("ix_customer_accounts_email", table_name="customer_accounts")
    op.drop_index("ix_customer_accounts_customer_id", table_name="customer_accounts")
    op.drop_index("ix_customer_accounts_store_id", table_name="customer_accounts")
    op.drop_table("customer_accounts")

    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_index("ix_orders_public_token")
        batch_op.drop_constraint("uq_orders_public_token", type_="unique")
        batch_op.drop_column("public_token")
