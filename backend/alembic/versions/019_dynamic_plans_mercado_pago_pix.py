"""dynamic plans and Mercado Pago Pix billing

Revision ID: 019_dynamic_plans_pix
Revises: 018_personalizados_segment
"""
from datetime import datetime, timezone
from decimal import Decimal
import json

from alembic import op
import sqlalchemy as sa

revision = "019_dynamic_plans_pix"
down_revision = "018_personalizados_segment"
branch_labels = None
depends_on = None


PLAN_SPECS = {
    "GRATUITO": {
        "name": "Gratuito",
        "monthly_price": Decimal("0.00"),
        "yearly_price": None,
        "description": "Plano interno de contingência da plataforma.",
        "limits": {"products": 20, "services": 10, "professionals": 1},
        "features": {"coupons": False, "promotions": False, "custom_branding": False, "reports": False, "priority_support": False, "custom_domain": False, "online_payments": False},
        "sort_order": 0,
        "is_public": False,
        "is_featured": False,
        "badge": None,
        "trial_days": 0,
        "grace_days": 0,
    },
    "ESSENCIAL": {
        "name": "Essencial",
        "monthly_price": Decimal("49.90"),
        "yearly_price": None,
        "description": "Para pequenos negócios que querem vender e atender com uma presença digital profissional.",
        "limits": {"products": 150, "services": 40, "professionals": 4},
        "features": {"coupons": True, "promotions": False, "custom_branding": True, "reports": False, "priority_support": False, "custom_domain": False, "online_payments": False},
        "sort_order": 1,
        "is_public": True,
        "is_featured": False,
        "badge": "Comece profissional",
        "trial_days": 7,
        "grace_days": 5,
    },
    "PROFISSIONAL": {
        "name": "Profissional",
        "monthly_price": Decimal("89.90"),
        "yearly_price": None,
        "description": "Para empresas em crescimento que precisam de marketing, relatórios e maior capacidade operacional.",
        "limits": {"products": 600, "services": 150, "professionals": 20},
        "features": {"coupons": True, "promotions": True, "custom_branding": True, "reports": True, "priority_support": False, "custom_domain": False, "online_payments": True},
        "sort_order": 2,
        "is_public": True,
        "is_featured": True,
        "badge": "Mais escolhido",
        "trial_days": 7,
        "grace_days": 5,
    },
    "PREMIUM": {
        "name": "Premium",
        "monthly_price": Decimal("149.90"),
        "yearly_price": None,
        "description": "Para operações maiores que querem todos os recursos, limites amplos e atendimento prioritário.",
        "limits": {"products": -1, "services": -1, "professionals": -1},
        "features": {"coupons": True, "promotions": True, "custom_branding": True, "reports": True, "priority_support": True, "custom_domain": True, "online_payments": True},
        "sort_order": 3,
        "is_public": True,
        "is_featured": False,
        "badge": "Tudo liberado",
        "trial_days": 7,
        "grace_days": 7,
    },
}


def upgrade():
    # Somente ADD COLUMN/INDEX: evita recriar tabelas SQLite que já possuem FKs
    # apontando para plans/subscriptions e mantém a migração segura também no PostgreSQL.
    op.add_column("plans", sa.Column("trial_days", sa.Integer(), nullable=False, server_default="7"))
    op.add_column("plans", sa.Column("grace_days", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("plans", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("plans", sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("plans", sa.Column("badge", sa.String(length=60), nullable=True))

    op.add_column("subscriptions", sa.Column("plan_name_snapshot", sa.String(length=80), nullable=True))
    op.add_column("subscriptions", sa.Column("monthly_price_snapshot", sa.Numeric(12, 2), nullable=True))
    op.add_column("subscriptions", sa.Column("yearly_price_snapshot", sa.Numeric(12, 2), nullable=True))
    op.add_column("subscriptions", sa.Column("limits_snapshot", sa.JSON(), nullable=True))
    op.add_column("subscriptions", sa.Column("features_snapshot", sa.JSON(), nullable=True))
    op.add_column("subscriptions", sa.Column("trial_days_snapshot", sa.Integer(), nullable=True))
    op.add_column("subscriptions", sa.Column("grace_days_snapshot", sa.Integer(), nullable=True))
    op.add_column("subscriptions", sa.Column("commercial_terms_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("subscription_invoices", sa.Column("provider_status", sa.String(length=80), nullable=True))
    op.add_column("subscription_invoices", sa.Column("provider_idempotency_key", sa.String(length=80), nullable=True))
    op.add_column("subscription_invoices", sa.Column("pix_qr_code", sa.Text(), nullable=True))
    op.add_column("subscription_invoices", sa.Column("pix_qr_code_base64", sa.Text(), nullable=True))
    op.add_column("subscription_invoices", sa.Column("pix_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_subscription_invoices_provider_idempotency_key", "subscription_invoices", ["provider_idempotency_key"], unique=True)

    connection = op.get_bind()
    now = datetime.now(timezone.utc)

    # Preserva IDs e assinaturas existentes: Básico vira Essencial e Empresa vira Premium.
    codes = {row[0] for row in connection.execute(sa.text("SELECT code FROM plans")).fetchall()}
    if "BASICO" in codes and "ESSENCIAL" not in codes:
        connection.execute(sa.text("UPDATE plans SET code='ESSENCIAL' WHERE code='BASICO'"))
    if "EMPRESA" in codes and "PREMIUM" not in codes:
        connection.execute(sa.text("UPDATE plans SET code='PREMIUM' WHERE code='EMPRESA'"))

    plans_table = sa.table(
        "plans",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("monthly_price", sa.Numeric(12, 2)),
        sa.column("yearly_price", sa.Numeric(12, 2)),
        sa.column("limits", sa.JSON),
        sa.column("features", sa.JSON),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        sa.column("trial_days", sa.Integer),
        sa.column("grace_days", sa.Integer),
        sa.column("is_public", sa.Boolean),
        sa.column("is_featured", sa.Boolean),
        sa.column("badge", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    for code, spec in PLAN_SPECS.items():
        row_id = connection.execute(sa.text("SELECT id FROM plans WHERE code=:code"), {"code": code}).scalar()
        values = dict(spec)
        values.update({"code": code, "is_active": True, "updated_at": now})
        if row_id is None:
            values.update({"created_at": now})
            connection.execute(sa.insert(plans_table).values(**values))
        else:
            connection.execute(sa.update(plans_table).where(plans_table.c.id == row_id).values(**values))

    # Congela as condições comerciais de assinaturas já existentes para que uma edição
    # futura do plano não altere silenciosamente clientes atuais. As colunas JSON usam
    # tipos SQLAlchemy explícitos para funcionar tanto em SQLite quanto em PostgreSQL.
    subscriptions_table = sa.table(
        "subscriptions",
        sa.column("id", sa.Integer),
        sa.column("plan_name_snapshot", sa.String),
        sa.column("monthly_price_snapshot", sa.Numeric(12, 2)),
        sa.column("yearly_price_snapshot", sa.Numeric(12, 2)),
        sa.column("limits_snapshot", sa.JSON),
        sa.column("features_snapshot", sa.JSON),
        sa.column("trial_days_snapshot", sa.Integer),
        sa.column("grace_days_snapshot", sa.Integer),
        sa.column("commercial_terms_at", sa.DateTime(timezone=True)),
    )
    rows = connection.execute(sa.text(
        """
        SELECT s.id, p.name, p.monthly_price, p.yearly_price, p.limits, p.features, p.trial_days, p.grace_days
        FROM subscriptions s JOIN plans p ON p.id = s.plan_id
        """
    )).mappings().all()
    def json_value(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value or {}

    for row in rows:
        connection.execute(
            sa.update(subscriptions_table)
            .where(subscriptions_table.c.id == row["id"])
            .values(
                plan_name_snapshot=row["name"],
                monthly_price_snapshot=row["monthly_price"],
                yearly_price_snapshot=row["yearly_price"],
                limits_snapshot=json_value(row["limits"]),
                features_snapshot=json_value(row["features"]),
                trial_days_snapshot=row["trial_days"],
                grace_days_snapshot=row["grace_days"],
                commercial_terms_at=now,
            )
        )


def downgrade():
    with op.batch_alter_table("subscription_invoices") as batch_op:
        batch_op.drop_index("ix_subscription_invoices_provider_idempotency_key")
        batch_op.drop_column("pix_expires_at")
        batch_op.drop_column("pix_qr_code_base64")
        batch_op.drop_column("pix_qr_code")
        batch_op.drop_column("provider_idempotency_key")
        batch_op.drop_column("provider_status")

    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_column("commercial_terms_at")
        batch_op.drop_column("grace_days_snapshot")
        batch_op.drop_column("trial_days_snapshot")
        batch_op.drop_column("features_snapshot")
        batch_op.drop_column("limits_snapshot")
        batch_op.drop_column("yearly_price_snapshot")
        batch_op.drop_column("monthly_price_snapshot")
        batch_op.drop_column("plan_name_snapshot")

    with op.batch_alter_table("plans") as batch_op:
        batch_op.drop_column("badge")
        batch_op.drop_column("is_featured")
        batch_op.drop_column("is_public")
        batch_op.drop_column("grace_days")
        batch_op.drop_column("trial_days")
