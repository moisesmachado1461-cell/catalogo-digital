from datetime import datetime, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models import (
    BusinessCategory,
    BusinessModel,
    Category,
    Inventory,
    Product,
    Store,
    User,
)
from app.security import hash_password
from app.utils.text import slugify


def main():
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        # Modelo VAREJO
        business_model = (
            db.query(BusinessModel)
            .filter(BusinessModel.code == "VAREJO")
            .one()
        )

        # Categoria de negócio: eletrônicos/informática
        business_category = (
            db.query(BusinessCategory)
            .filter(
                BusinessCategory.slug == "loja-eletronicos-informatica"
            )
            .one()
        )

        # Segunda loja
        store = (
            db.query(Store)
            .filter(Store.slug == "loja-tech-demo")
            .first()
        )

        if not store:
            store = Store(
                name="Loja Tech Demo",
                slug="loja-tech-demo",
                business_category_id=business_category.id,
                business_model_id=business_model.id,
                capabilities={
                    **business_model.default_capabilities,
                    "coupons": True,
                    "promotions": True,
                },
                description="Segunda loja usada para testar o multi-tenant.",
                primary_color="#2563EB",
                secondary_color="#0F172A",
                is_active=True,
                created_at=now,
                updated_at=now,
            )

            db.add(store)
            db.flush()

        # Administrador exclusivo da segunda loja
        admin = (
            db.query(User)
            .filter(User.email == "admin@lojatechdemo.com")
            .first()
        )

        if not admin:
            admin = User(
                name="Administrador Loja Tech",
                email="admin@lojatechdemo.com",
                password_hash=hash_password("Admin@67890"),
                role="ADMINISTRADOR_DA_LOJA",
                store_id=store.id,
                is_active=True,
                email_verified=True,
                created_at=now,
                updated_at=now,
            )

            db.add(admin)

        # Categoria interna da loja
        category = (
            db.query(Category)
            .filter(
                Category.store_id == store.id,
                Category.slug == "acessorios"
            )
            .first()
        )

        if not category:
            category = Category(
                store_id=store.id,
                name="Acessórios",
                slug="acessorios",
                description="Acessórios de informática.",
                sort_order=1,
                is_active=True,
                created_at=now,
                updated_at=now,
            )

            db.add(category)
            db.flush()

        # Produto exclusivo da segunda loja
        product = (
            db.query(Product)
            .filter(
                Product.store_id == store.id,
                Product.sku == "TECH-001"
            )
            .first()
        )

        if not product:
            product = Product(
                store_id=store.id,
                category_id=category.id,
                name="Mouse Gamer Demo",
                slug=slugify("Mouse Gamer Demo"),
                description="Produto exclusivo da Loja Tech Demo.",
                sku="TECH-001",
                price=Decimal("99.90"),
                is_active=True,
                track_inventory=True,
                created_at=now,
                updated_at=now,
            )

            db.add(product)
            db.flush()

        inventory = (
            db.query(Inventory)
            .filter(
                Inventory.store_id == store.id,
                Inventory.product_id == product.id,
                Inventory.variant_id.is_(None),
            )
            .first()
        )

        if not inventory:
            inventory = Inventory(
                store_id=store.id,
                product_id=product.id,
                variant_id=None,
                quantity=10,
                reserved_quantity=0,
                min_quantity=2,
                updated_at=now,
            )

            db.add(inventory)

        db.commit()

        print("Segunda loja criada com sucesso.")
        print(f"Loja: {store.name}")
        print(f"store_id: {store.id}")
        print("Admin: admin@lojatechdemo.com")
        print("Senha de desenvolvimento: Admin@67890")
        print("Produto: Mouse Gamer Demo")
        print(f"product_id: {product.id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
    