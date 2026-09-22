"""security and lgpd foundation

Revision ID: 010_security_lgpd
Revises: 009_plans_subscriptions
"""
from alembic import op
import sqlalchemy as sa

revision = "010_security_lgpd"
down_revision = "009_plans_subscriptions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_login_ip", sa.String(64), nullable=True))

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=True),
        sa.Column("entity_id", sa.String(80), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for col in ["store_id", "user_id", "action", "entity_type", "entity_id", "created_at"]:
        op.create_index(f"ix_audit_logs_{col}", "audit_logs", [col])

    op.create_table(
        "privacy_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("protocol", sa.String(64), nullable=False),
        sa.Column("request_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDENTE"),
        sa.Column("customer_name", sa.String(120), nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("customer_phone", sa.String(40), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("protocol", name="uq_privacy_requests_protocol"),
    )
    for col in ["store_id", "protocol", "request_type", "status", "customer_email", "customer_phone", "created_at"]:
        op.create_index(f"ix_privacy_requests_{col}", "privacy_requests", [col], unique=(col == "protocol"))


def downgrade():
    op.drop_table("privacy_requests")
    op.drop_table("audit_logs")
    op.drop_column("users", "last_login_ip")
    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
