from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.catalog import Category, Product, ProductOption, ProductOptionItem, ProductVariant
from ..models.sales import Inventory
from ..repositories.catalog_repository import get_product_for_store, get_store_by_slug
from ..schemas.catalog import (
    CategoryCreate,
    CategoryUpdate,
    InventoryUpdate,
    OptionCreate,
    OptionUpdate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)
from ..services.subscription_service import enforce_limit
from ..services.catalog_service import (
    add_option,
    add_variant,
    create_category,
    create_product,
    update_category,
    update_product,
)

public_router = APIRouter(prefix="/api/public", tags=["catalog-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["catalog-admin"])


def _inventory_dict(row: Inventory | None):
    if not row:
        return None
    return {
        "id": row.id,
        "product_id": row.product_id,
        "variant_id": row.variant_id,
        "quantity": row.quantity,
        "reserved_quantity": row.reserved_quantity,
        "min_quantity": row.min_quantity,
    }


def _variant_dict(v: ProductVariant, inventory_rows: list[Inventory]):
    inv = next((i for i in inventory_rows if i.variant_id == v.id), None)
    return {
        "id": v.id,
        "name": v.name,
        "sku": v.sku,
        "price": v.price,
        "sort_order": v.sort_order,
        "is_active": v.is_active,
        "inventory": _inventory_dict(inv),
    }


def _option_dict(option: ProductOption):
    return {
        "id": option.id,
        "name": option.name,
        "required": option.required,
        "min_selections": option.min_selections,
        "max_selections": option.max_selections,
        "sort_order": option.sort_order,
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "price_adjustment": item.price_adjustment,
                "sort_order": item.sort_order,
                "is_active": item.is_active,
            }
            for item in sorted(option.items, key=lambda x: (x.sort_order, x.id))
            if item.is_active
        ],
    }


def _product_dict(product: Product):
    base_inventory = next((i for i in product.inventory_rows if i.variant_id is None), None)
    return {
        "id": product.id,
        "category_id": product.category_id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "sku": product.sku,
        "price": product.price,
        "compare_at_price": product.compare_at_price,
        "image_url": product.image_url,
        "is_active": product.is_active,
        "track_inventory": product.track_inventory,
        "inventory": _inventory_dict(base_inventory),
        "variants": [
            _variant_dict(v, product.inventory_rows)
            for v in sorted(product.variants, key=lambda x: (x.sort_order, x.id))
            if v.is_active
        ],
        "options": [
            _option_dict(o)
            for o in sorted(product.options, key=lambda x: (x.sort_order, x.id))
            if o.is_active
        ],
    }


@public_router.get("/stores/{slug}/catalog")
def public_catalog(slug: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    if not store.capabilities.get("catalog", False):
        raise HTTPException(status_code=404, detail="Catálogo não habilitado para esta loja")

    categories = (
        db.query(Category)
        .filter(Category.store_id == store.id, Category.is_active.is_(True))
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    products = (
        db.query(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.options).selectinload(ProductOption.items),
            selectinload(Product.inventory_rows),
        )
        .filter(Product.store_id == store.id, Product.is_active.is_(True))
        .order_by(Product.name)
        .all()
    )

    return {
        "store": {
            "id": store.id,
            "name": store.name,
            "slug": store.slug,
            "description": store.description,
            "logo_url": store.logo_url,
            "banner_url": store.banner_url,
            "primary_color": store.primary_color,
            "secondary_color": store.secondary_color,
            "whatsapp": store.whatsapp,
            "capabilities": store.capabilities,
        },
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "image_url": c.image_url,
                "sort_order": c.sort_order,
            }
            for c in categories
        ],
        "products": [_product_dict(p) for p in products],
    }


@admin_router.get("/categories")
def list_admin_categories(
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(Category)
        .filter(Category.store_id == store_id)
        .order_by(Category.sort_order, Category.name)
        .all()
    )


@admin_router.post("/categories", status_code=201)
def create_admin_category(
    data: CategoryCreate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    return create_category(db, store_id, data)


@admin_router.put("/categories/{category_id}")
def update_admin_category(
    category_id: int,
    data: CategoryUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    return update_category(db, store_id, category_id, data)


@admin_router.delete("/categories/{category_id}")
def deactivate_admin_category(
    category_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.store_id == store_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    category.is_active = False
    db.commit()
    return {"ok": True, "message": "Categoria desativada"}


@admin_router.get("/products")
def list_admin_products(
    include_inactive: bool = Query(default=True),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.options).selectinload(ProductOption.items),
            selectinload(Product.inventory_rows),
        )
        .filter(Product.store_id == store_id)
    )
    if not include_inactive:
        query = query.filter(Product.is_active.is_(True))
    return [_product_dict(p) for p in query.order_by(Product.name).all()]


@admin_router.post("/products", status_code=201)
def create_admin_product(
    data: ProductCreate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    enforce_limit(db, store_id, "products")
    product = create_product(db, store_id, data)
    product = (
        db.query(Product)
        .options(selectinload(Product.inventory_rows), selectinload(Product.variants), selectinload(Product.options).selectinload(ProductOption.items))
        .filter(Product.id == product.id, Product.store_id == store_id)
        .one()
    )
    return _product_dict(product)


@admin_router.get("/products/{product_id}")
def get_admin_product(
    product_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.options).selectinload(ProductOption.items),
            selectinload(Product.inventory_rows),
        )
        .filter(Product.id == product_id, Product.store_id == store_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return _product_dict(product)


@admin_router.put("/products/{product_id}")
def update_admin_product(
    product_id: int,
    data: ProductUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    current = get_product_for_store(db, product_id, store_id)
    if not current:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if data.is_active is True and not current.is_active:
        enforce_limit(db, store_id, "products")
    update_product(db, store_id, product_id, data)
    return get_admin_product(product_id, store_id, db)


@admin_router.delete("/products/{product_id}")
def deactivate_admin_product(
    product_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    product = get_product_for_store(db, product_id, store_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    product.is_active = False
    db.commit()
    return {"ok": True, "message": "Produto desativado"}


@admin_router.post("/products/{product_id}/variants", status_code=201)
def create_product_variant(
    product_id: int,
    data: VariantCreate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    variant = add_variant(db, store_id, product_id, data)
    return {
        "id": variant.id,
        "product_id": variant.product_id,
        "name": variant.name,
        "sku": variant.sku,
        "price": variant.price,
        "sort_order": variant.sort_order,
    }


@admin_router.post("/products/{product_id}/options", status_code=201)
def create_product_option(
    product_id: int,
    data: OptionCreate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    option = add_option(db, store_id, product_id, data)
    option = (
        db.query(ProductOption)
        .options(selectinload(ProductOption.items))
        .filter(ProductOption.id == option.id, ProductOption.store_id == store_id)
        .one()
    )
    return _option_dict(option)


@admin_router.put("/products/{product_id}/variants/{variant_id}")
def update_product_variant(
    product_id: int, variant_id: int, data: VariantUpdate,
    store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db),
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id, ProductVariant.product_id == product_id, ProductVariant.store_id == store_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variante não encontrada")
    for key, value in data.model_dump().items(): setattr(variant, key, value)
    db.commit(); db.refresh(variant)
    return {"id": variant.id, "product_id": variant.product_id, "name": variant.name, "sku": variant.sku, "price": variant.price, "sort_order": variant.sort_order, "is_active": variant.is_active}


@admin_router.delete("/products/{product_id}/variants/{variant_id}")
def deactivate_product_variant(
    product_id: int, variant_id: int, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db),
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id, ProductVariant.product_id == product_id, ProductVariant.store_id == store_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variante não encontrada")
    variant.is_active = False; db.commit(); return {"ok": True}


@admin_router.put("/products/{product_id}/options/{option_id}")
def update_product_option(
    product_id: int, option_id: int, data: OptionUpdate,
    store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db),
):
    option = db.query(ProductOption).options(selectinload(ProductOption.items)).filter(ProductOption.id == option_id, ProductOption.product_id == product_id, ProductOption.store_id == store_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Grupo de adicionais não encontrado")
    option.name = data.name; option.required = data.required; option.min_selections = data.min_selections; option.max_selections = data.max_selections; option.sort_order = data.sort_order; option.is_active = data.is_active
    db.query(ProductOptionItem).filter(ProductOptionItem.product_option_id == option.id, ProductOptionItem.store_id == store_id).delete(synchronize_session=False)
    for item in data.items:
        db.add(ProductOptionItem(store_id=store_id, product_option_id=option.id, name=item.name, price_adjustment=item.price_adjustment, sort_order=item.sort_order, is_active=True))
    db.commit()
    option = db.query(ProductOption).options(selectinload(ProductOption.items)).filter(ProductOption.id == option.id).one()
    return _option_dict(option)


@admin_router.delete("/products/{product_id}/options/{option_id}")
def deactivate_product_option(
    product_id: int, option_id: int, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db),
):
    option = db.query(ProductOption).filter(ProductOption.id == option_id, ProductOption.product_id == product_id, ProductOption.store_id == store_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Grupo de adicionais não encontrado")
    option.is_active = False; db.commit(); return {"ok": True}


@admin_router.get("/inventory")
def list_inventory(
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Inventory)
        .filter(Inventory.store_id == store_id)
        .order_by(Inventory.product_id, Inventory.variant_id)
        .all()
    )
    return [_inventory_dict(row) for row in rows]


@admin_router.patch("/inventory/{inventory_id}")
def update_inventory(
    inventory_id: int,
    data: InventoryUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    row = (
        db.query(Inventory)
        .filter(Inventory.id == inventory_id, Inventory.store_id == store_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Estoque não encontrado")
    row.quantity = data.quantity
    if data.min_quantity is not None:
        row.min_quantity = data.min_quantity
    db.commit()
    db.refresh(row)
    return _inventory_dict(row)
