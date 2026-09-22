"""booking experience: public appointment token and professional blocks

Revision ID: 006_booking_experience
Revises: 005_marketing_checkout
"""
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "006_booking_experience"
down_revision = "005_marketing_checkout"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("appointments", sa.Column("public_token", sa.String(length=80), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id FROM appointments WHERE public_token IS NULL")).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE appointments SET public_token = :token WHERE id = :id"),
            {"token": uuid4().hex, "id": row[0]},
        )

    with op.batch_alter_table("appointments") as batch:
        batch.alter_column("public_token", existing_type=sa.String(length=80), nullable=False)
    op.create_index("ix_appointments_public_token", "appointments", ["public_token"], unique=True)

    op.create_table(
        "professional_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("professional_id", sa.Integer(), sa.ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="ck_professional_blocks_time_order"),
    )
    op.create_index("ix_professional_blocks_store_id", "professional_blocks", ["store_id"])
    op.create_index("ix_professional_blocks_professional_id", "professional_blocks", ["professional_id"])
    op.create_index("ix_professional_blocks_starts_at", "professional_blocks", ["starts_at"])


def downgrade():
    op.drop_index("ix_professional_blocks_starts_at", table_name="professional_blocks")
    op.drop_index("ix_professional_blocks_professional_id", table_name="professional_blocks")
    op.drop_index("ix_professional_blocks_store_id", table_name="professional_blocks")
    op.drop_table("professional_blocks")

    op.drop_index("ix_appointments_public_token", table_name="appointments")
    with op.batch_alter_table("appointments") as batch:
        batch.drop_column("public_token")
