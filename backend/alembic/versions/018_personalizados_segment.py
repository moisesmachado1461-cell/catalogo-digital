"""segmento de estamparia, personalizados e brindes

Revision ID: 018_personalizados_segment
Revises: 017_customer_portal
"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "018_personalizados_segment"
down_revision = "017_customer_portal"
branch_labels = None
depends_on = None

SLUG = "estamparia-personalizados-brindes"
CAPABILITIES = {
    "catalog": True,
    "services": True,
    "cart": True,
    "checkout": True,
    "inventory": True,
    "quotes": True,
    "payments": True,
    "delivery": True,
    "coupons": True,
    "promotions": True,
}


def upgrade():
    connection = op.get_bind()
    hybrid_id = connection.execute(
        sa.text("SELECT id FROM business_models WHERE code = :code"),
        {"code": "HIBRIDO"},
    ).scalar()
    # Em banco novo, os modelos de negócio são criados pelo seed executado
    # depois das migrations. Nesse caso a migration apenas prepara a cadeia;
    # o próprio seed adicionará esta categoria. Em bancos já existentes
    # (produção), o HIBRIDO já existe e a categoria é inserida aqui.
    if hybrid_id is None:
        return

    existing = connection.execute(
        sa.text("SELECT id FROM business_categories WHERE slug = :slug"),
        {"slug": SLUG},
    ).scalar()

    categories = sa.table(
        "business_categories",
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("description", sa.Text),
        sa.column("business_model_id", sa.Integer),
        sa.column("default_capabilities", sa.JSON),
        sa.column("icon", sa.String),
        sa.column("image_url", sa.String),
        sa.column("active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    max_order = connection.execute(
        sa.text("SELECT COALESCE(MAX(sort_order), 0) FROM business_categories")
    ).scalar() or 0

    values = {
        "name": "Estamparia / Personalizados / Brindes",
        "slug": SLUG,
        "description": (
            "Negócios que vendem produtos prontos e também produzem itens personalizados, "
            "estampas, brindes e trabalhos sob encomenda/orçamento."
        ),
        "business_model_id": hybrid_id,
        "default_capabilities": CAPABILITIES,
        "icon": "palette",
        "image_url": None,
        "active": True,
        "sort_order": int(max_order) + 1,
        "created_at": now,
        "updated_at": now,
    }

    if existing is None:
        connection.execute(sa.insert(categories).values(**values))
    else:
        connection.execute(
            sa.update(categories).where(sa.column("slug") == SLUG).values(**{
                key: value for key, value in values.items() if key not in {"slug", "created_at"}
            })
        )


def downgrade():
    connection = op.get_bind()
    category_id = connection.execute(
        sa.text("SELECT id FROM business_categories WHERE slug = :slug"),
        {"slug": SLUG},
    ).scalar()
    if category_id is None:
        return

    in_use = connection.execute(
        sa.text("SELECT COUNT(*) FROM stores WHERE business_category_id = :category_id"),
        {"category_id": category_id},
    ).scalar() or 0
    if in_use:
        connection.execute(
            sa.text("UPDATE business_categories SET active = :active WHERE id = :category_id"),
            {"active": False, "category_id": category_id},
        )
    else:
        connection.execute(
            sa.text("DELETE FROM business_categories WHERE id = :category_id"),
            {"category_id": category_id},
        )
