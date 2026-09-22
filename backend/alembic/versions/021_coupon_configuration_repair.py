"""repair coupon capabilities and active subscription feature snapshots

Revision ID: 021_coupon_configuration_repair
Revises: 020_store_marketplace_payments
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "021_coupon_configuration_repair"
down_revision = "020_store_marketplace_payments"
branch_labels = None
depends_on = None


def _json_dict(value):
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}
    return {}


def upgrade():
    connection = op.get_bind()

    # Uma loja que já possui cupons cadastrados declarou explicitamente o uso
    # desse recurso. Corrige registros antigos cujo JSON de capacidades não
    # recebeu a chave "coupons".
    stores = sa.table(
        "stores",
        sa.column("id", sa.Integer),
        sa.column("capabilities", sa.JSON),
    )
    coupon_store_ids = {
        int(row[0])
        for row in connection.execute(sa.text("SELECT DISTINCT store_id FROM coupons")).fetchall()
    }
    if coupon_store_ids:
        rows = connection.execute(
            sa.select(stores.c.id, stores.c.capabilities).where(stores.c.id.in_(coupon_store_ids))
        ).fetchall()
        for store_id, raw_capabilities in rows:
            capabilities = _json_dict(raw_capabilities)
            if not capabilities.get("coupons", False):
                capabilities["coupons"] = True
                connection.execute(
                    stores.update().where(stores.c.id == store_id).values(capabilities=capabilities)
                )

    # Planos editáveis são a fonte atual dos recursos e limites. Atualiza as
    # assinaturas vigentes, preservando os preços comerciais já contratados.
    plans = sa.table(
        "plans",
        sa.column("id", sa.Integer),
        sa.column("features", sa.JSON),
        sa.column("limits", sa.JSON),
    )
    subscriptions = sa.table(
        "subscriptions",
        sa.column("id", sa.Integer),
        sa.column("plan_id", sa.Integer),
        sa.column("status", sa.String),
        sa.column("features_snapshot", sa.JSON),
        sa.column("limits_snapshot", sa.JSON),
    )
    active_rows = connection.execute(
        sa.select(subscriptions.c.id, plans.c.features, plans.c.limits)
        .select_from(subscriptions.join(plans, subscriptions.c.plan_id == plans.c.id))
        .where(subscriptions.c.status.in_(["TRIAL", "ACTIVE", "PAST_DUE"]))
    ).fetchall()
    for subscription_id, features, limits in active_rows:
        connection.execute(
            subscriptions.update()
            .where(subscriptions.c.id == subscription_id)
            .values(features_snapshot=_json_dict(features), limits_snapshot=_json_dict(limits))
        )


def downgrade():
    # Migração de reparo de dados: não remove permissões ou snapshots válidos.
    pass
