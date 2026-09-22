"""quote requests and attachments

Revision ID: 004_quotes
Revises: 003_services_appointments
"""
from alembic import op
import sqlalchemy as sa

revision = "004_quotes"
down_revision = "003_services_appointments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quote_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("public_token", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("preferred_contact", sa.String(length=20), nullable=False, server_default="WHATSAPP"),
        sa.Column("service_address", sa.String(length=255), nullable=True),
        sa.Column("service_city", sa.String(length=120), nullable=True),
        sa.Column("service_state", sa.String(length=2), nullable=True),
        sa.Column("service_zip_code", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RECEBIDO"),
        sa.Column("estimated_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("response_message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("public_token", name="uq_quote_requests_public_token"),
        sa.CheckConstraint("estimated_amount IS NULL OR estimated_amount >= 0", name="ck_quote_requests_estimated_amount_nonnegative"),
    )
    op.create_index("ix_quote_requests_store_id", "quote_requests", ["store_id"])
    op.create_index("ix_quote_requests_customer_id", "quote_requests", ["customer_id"])
    op.create_index("ix_quote_requests_service_id", "quote_requests", ["service_id"])
    op.create_index("ix_quote_requests_public_token", "quote_requests", ["public_token"])
    op.create_index("ix_quote_requests_status", "quote_requests", ["status"])
    op.create_index("ix_quote_requests_created_at", "quote_requests", ["created_at"])

    op.create_table(
        "quote_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quote_request_id", sa.Integer(), sa.ForeignKey("quote_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.String(length=1000), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quote_attachments_store_id", "quote_attachments", ["store_id"])
    op.create_index("ix_quote_attachments_quote_request_id", "quote_attachments", ["quote_request_id"])


def downgrade():
    op.drop_index("ix_quote_attachments_quote_request_id", table_name="quote_attachments")
    op.drop_index("ix_quote_attachments_store_id", table_name="quote_attachments")
    op.drop_table("quote_attachments")

    op.drop_index("ix_quote_requests_created_at", table_name="quote_requests")
    op.drop_index("ix_quote_requests_status", table_name="quote_requests")
    op.drop_index("ix_quote_requests_public_token", table_name="quote_requests")
    op.drop_index("ix_quote_requests_service_id", table_name="quote_requests")
    op.drop_index("ix_quote_requests_customer_id", table_name="quote_requests")
    op.drop_index("ix_quote_requests_store_id", table_name="quote_requests")
    op.drop_table("quote_requests")
