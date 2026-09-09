from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.catalog import Category, Product, ProductOption, ProductOptionItem, ProductVariant
from ..models.sales import Inventory
from ..repositories.catalog_repository import get_category_for_store, get_product_for_store
from ..schemas.catalog import CategoryCreate, CategoryUpdate, OptionCreate, ProductCreate, ProductUpdate, VariantCreate
from ..utils.text import slugify


def _commit_or_conflict(db: Session, detail: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail)


def create_category(db: Session, store_id: int, data: CategoryCreate) -> Category:
    slug = slugify(data.slug or data.name)
    category = Category(
        store_id=store_id,
        name=data.name.strip(),
        slug=slug,
        description=data.description,
        image_url=data.image_url,
        sort_order=data.sort_order,
        is_active=True,
    )
    db.add(category)
    _commit_or_conflict(db, "Já existe uma categoria com esse slug nesta loja")
    db.refresh(category)
    return category


def update_category(db: Session, store_id: int, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category_for_store(db, category_id, store_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    values = data.model_dump(exclude_unset=True)
    if "name" in values and values["name"] is not None:
        values["name"] = values["name"].strip()
    if "slug" in values and values["slug"] is not None:
        values["slug"] = slugify(values["slug"])
    for key, value in values.items():
        setattr(category, key, value)
    _commit_or_conflict(db, "Já existe uma categoria com esse slug nesta loja")
    db.refresh(category)
    return category


def create_product(db: Session, store_id: int, data: ProductCreate) -> Product:
    if data.category_id is not None and not get_category_for_store(db, data.category_id, store_id):
        raise HTTPException(status_code=400, detail="A categoria não pertence à sua loja")

    product = Product(
        store_id=store_id,
        category_id=data.category_id,
        name=data.name.strip(),
        slug=slugify(data.slug or data.name),
        description=data.description,
        sku=(data.sku.strip() if data.sku else None),
        price=data.price,
        compare_at_price=data.compare_at_price,
        image_url=data.image_url,
        is_active=True,
        track_inventory=data.track_inventory,
    )
    db.add(product)
    try:
        db.flush()
        if product.track_inventory:
            db.add(
                Inventory(
                    store_id=store_id,
                    product_id=product.id,
                    variant_id=None,
                    quantity=data.initial_stock,
                    reserved_quantity=0,
                    min_quantity=data.min_stock,
                )
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Slug ou SKU já utilizado nesta loja")
    db.refresh(product)
    return product


def update_product(db: Session, store_id: int, product_id: int, data: ProductUpdate) -> Product:
    product = get_product_for_store(db, product_id, store_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    values = data.model_dump(exclude_unset=True)
    if "category_id" in values and values["category_id"] is not None:
        if not get_category_for_store(db, values["category_id"], store_id):
            raise HTTPException(status_code=400, detail="A categoria não pertence à sua loja")
    if "name" in values and values["name"] is not None:
        values["name"] = values["name"].strip()
    if "slug" in values and values["slug"] is not None:
        values["slug"] = slugify(values["slug"])
    if "sku" in values and values["sku"] is not None:
        values["sku"] = values["sku"].strip() or None

    for key, value in values.items():
        setattr(product, key, value)

    if product.track_inventory:
        inv = (
            db.query(Inventory)
            .filter(
                Inventory.store_id == store_id,
                Inventory.product_id == product.id,
                Inventory.variant_id.is_(None),
            )
            .first()
        )
        if not inv:
            db.add(Inventory(store_id=store_id, product_id=product.id, quantity=0, reserved_quantity=0, min_quantity=0))

    _commit_or_conflict(db, "Slug ou SKU já utilizado nesta loja")
    db.refresh(product)
    return product


def add_variant(db: Session, store_id: int, product_id: int, data: VariantCreate) -> ProductVariant:
    product = get_product_for_store(db, product_id, store_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    variant = ProductVariant(
        store_id=store_id,
        product_id=product.id,
        name=data.name.strip(),
        sku=(data.sku.strip() if data.sku else None),
        price=data.price,
        sort_order=data.sort_order,
        is_active=True,
    )
    db.add(variant)
    try:
        db.flush()
        if product.track_inventory:
            db.add(
                Inventory(
                    store_id=store_id,
                    product_id=product.id,
                    variant_id=variant.id,
                    quantity=data.initial_stock,
                    reserved_quantity=0,
                    min_quantity=data.min_stock,
                )
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU da variante já utilizado nesta loja")
    db.refresh(variant)
    return variant


def add_option(db: Session, store_id: int, product_id: int, data: OptionCreate) -> ProductOption:
    product = get_product_for_store(db, product_id, store_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if data.max_selections < data.min_selections:
        raise HTTPException(status_code=400, detail="max_selections deve ser maior ou igual a min_selections")

    option = ProductOption(
        store_id=store_id,
        product_id=product.id,
        name=data.name.strip(),
        required=data.required,
        min_selections=data.min_selections,
        max_selections=data.max_selections,
        sort_order=data.sort_order,
        is_active=True,
    )
    db.add(option)
    db.flush()
    for item in data.items:
        db.add(
            ProductOptionItem(
                store_id=store_id,
                product_option_id=option.id,
                name=item.name.strip(),
                price_adjustment=item.price_adjustment or Decimal("0.00"),
                sort_order=item.sort_order,
                is_active=True,
            )
        )
    db.commit()
    db.refresh(option)
    return option
