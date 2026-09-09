from sqlalchemy.orm import Session

from ..models.catalog import Category, Product
from ..models.store import Store


def get_store_by_slug(db: Session, slug: str) -> Store | None:
    return db.query(Store).filter(Store.slug == slug, Store.is_active.is_(True)).first()


def get_category_for_store(db: Session, category_id: int, store_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id, Category.store_id == store_id).first()


def get_product_for_store(db: Session, product_id: int, store_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id, Product.store_id == store_id).first()
