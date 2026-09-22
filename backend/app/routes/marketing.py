from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.catalog import Product
from ..models.marketing import Coupon, CouponProduct, Promotion, PromotionItem
from ..repositories.catalog_repository import get_store_by_slug
from ..schemas.marketing import CouponCreate, CouponPreviewRequest, CouponUpdate, PromotionCreate, PromotionUpdate
from ..services.marketing_service import active_promotions_for_store, active_public_coupons_for_store, validate_coupon
from ..services.subscription_service import feature_enabled, require_feature

public_router = APIRouter(prefix="/api/public", tags=["marketing-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["marketing-admin"])


def coupon_dict(db: Session, c: Coupon):
    product_ids = [
        row.product_id
        for row in db.query(CouponProduct).filter(
            CouponProduct.store_id == c.store_id, CouponProduct.coupon_id == c.id
        ).order_by(CouponProduct.product_id).all()
    ]
    return {
        "id": c.id, "code": c.code, "description": c.description, "discount_type": c.discount_type,
        "value": c.value, "min_order_value": c.min_order_value, "max_discount": c.max_discount,
        "starts_at": c.starts_at.isoformat() if c.starts_at else None,
        "ends_at": c.ends_at.isoformat() if c.ends_at else None,
        "usage_limit": c.usage_limit, "usage_count": c.usage_count, "is_active": c.is_active,
        "is_public": c.is_public, "product_ids": product_ids, "scope": "PRODUCTS" if product_ids else "ORDER",
    }


def _validate_coupon_products(db: Session, store_id: int, product_ids: list[int]) -> list[int]:
    unique = sorted({int(product_id) for product_id in product_ids if int(product_id) > 0})
    if not unique:
        return []
    rows = db.query(Product.id).filter(Product.store_id == store_id, Product.id.in_(unique)).all()
    if len(rows) != len(unique):
        raise HTTPException(status_code=400, detail="Há produtos inválidos ou pertencentes a outra loja")
    return unique


def _sync_coupon_products(db: Session, coupon: Coupon, store_id: int, product_ids: list[int]) -> None:
    db.query(CouponProduct).filter(
        CouponProduct.coupon_id == coupon.id, CouponProduct.store_id == store_id
    ).delete(synchronize_session=False)
    now = datetime.now(timezone.utc)
    for product_id in _validate_coupon_products(db, store_id, product_ids):
        db.add(CouponProduct(store_id=store_id, coupon_id=coupon.id, product_id=product_id, created_at=now))


def promotion_dict(db: Session, p: Promotion):
    product_ids = [row.product_id for row in db.query(PromotionItem).filter(PromotionItem.store_id == p.store_id, PromotionItem.promotion_id == p.id).all()]
    return {
        "id": p.id, "name": p.name, "description": p.description, "discount_type": p.discount_type,
        "value": p.value, "product_ids": product_ids, "starts_at": p.starts_at.isoformat() if p.starts_at else None,
        "ends_at": p.ends_at.isoformat() if p.ends_at else None, "is_active": p.is_active,
    }


@public_router.get("/stores/{slug}/promotions")
def public_promotions(slug: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    if not store.capabilities.get("promotions", False) or not feature_enabled(db, store.id, "promotions"):
        return []
    return active_promotions_for_store(db, store.id)


@public_router.get("/stores/{slug}/coupons")
def public_coupons(slug: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    if not store.capabilities.get("coupons", False) or not feature_enabled(db, store.id, "coupons"):
        return []
    return active_public_coupons_for_store(db, store.id)


@public_router.post("/stores/{slug}/coupons/validate")
def public_validate_coupon(slug: str, data: CouponPreviewRequest, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    if not store.capabilities.get("coupons", False) or not feature_enabled(db, store.id, "coupons"):
        raise HTTPException(status_code=403, detail="Cupons não estão disponíveis nesta loja")
    product_totals: dict[int, Decimal] = {}
    for item in data.items:
        product_totals[item.product_id] = product_totals.get(item.product_id, Decimal("0.00")) + item.line_total
    coupon, discount = validate_coupon(db, store.id, data.code, data.subtotal, product_line_totals=product_totals)
    total = max(Decimal("0.00"), data.subtotal - discount)
    return {
        "valid": True,
        "code": coupon.code,
        "description": coupon.description,
        "discount_amount": discount,
        "subtotal": data.subtotal,
        "total": total,
        "scope": "PRODUCTS" if db.query(CouponProduct.id).filter(CouponProduct.store_id == store.id, CouponProduct.coupon_id == coupon.id).first() else "ORDER",
    }


@admin_router.get("/coupons")
def list_coupons(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "coupons")
    return [coupon_dict(db, c) for c in db.query(Coupon).filter(Coupon.store_id == store_id).order_by(Coupon.id.desc()).all()]


@admin_router.post("/coupons", status_code=status.HTTP_201_CREATED)
def create_coupon(data: CouponCreate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "coupons")
    if data.discount_type == "PERCENT" and data.value > 100:
        raise HTTPException(status_code=400, detail="Percentual não pode ultrapassar 100%")
    if db.query(Coupon.id).filter(Coupon.store_id == store_id, Coupon.code == data.code).first():
        raise HTTPException(status_code=409, detail="Já existe um cupom com este código")
    payload = data.model_dump(exclude={"product_ids"})
    c = Coupon(store_id=store_id, **payload)
    db.add(c); db.flush()
    _sync_coupon_products(db, c, store_id, data.product_ids)
    db.commit(); db.refresh(c)
    return coupon_dict(db, c)


@admin_router.put("/coupons/{coupon_id}")
def update_coupon(coupon_id: int, data: CouponUpdate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "coupons")
    c = db.query(Coupon).filter(Coupon.id == coupon_id, Coupon.store_id == store_id).first()
    if not c: raise HTTPException(status_code=404, detail="Cupom não encontrado")
    if data.discount_type == "PERCENT" and data.value > 100:
        raise HTTPException(status_code=400, detail="Percentual não pode ultrapassar 100%")
    duplicate = db.query(Coupon.id).filter(Coupon.store_id == store_id, Coupon.code == data.code, Coupon.id != coupon_id).first()
    if duplicate: raise HTTPException(status_code=409, detail="Já existe um cupom com este código")
    for k, v in data.model_dump(exclude={"product_ids"}).items(): setattr(c, k, v)
    _sync_coupon_products(db, c, store_id, data.product_ids)
    db.commit(); db.refresh(c); return coupon_dict(db, c)


@admin_router.delete("/coupons/{coupon_id}")
def deactivate_coupon(coupon_id: int, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "coupons")
    c = db.query(Coupon).filter(Coupon.id == coupon_id, Coupon.store_id == store_id).first()
    if not c: raise HTTPException(status_code=404, detail="Cupom não encontrado")
    c.is_active = False; db.commit(); return {"ok": True}


@admin_router.get("/promotions")
def list_promotions(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "promotions")
    return [promotion_dict(db, p) for p in db.query(Promotion).filter(Promotion.store_id == store_id).order_by(Promotion.id.desc()).all()]


def _validate_products(db: Session, store_id: int, product_ids: list[int]):
    unique = sorted(set(product_ids))
    count = db.query(Product.id).filter(Product.store_id == store_id, Product.id.in_(unique)).count()
    if count != len(unique): raise HTTPException(status_code=400, detail="Há produtos inválidos ou pertencentes a outra loja")
    return unique


def _sync_promotion_items(db: Session, promotion: Promotion, store_id: int, product_ids: list[int]):
    db.query(PromotionItem).filter(PromotionItem.promotion_id == promotion.id, PromotionItem.store_id == store_id).delete(synchronize_session=False)
    now = datetime.now(timezone.utc)
    for product_id in _validate_products(db, store_id, product_ids):
        db.add(PromotionItem(store_id=store_id, promotion_id=promotion.id, product_id=product_id, created_at=now))


@admin_router.post("/promotions", status_code=status.HTTP_201_CREATED)
def create_promotion(data: PromotionCreate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "promotions")
    if data.discount_type == "PERCENT" and data.value > 100: raise HTTPException(status_code=400, detail="Percentual não pode ultrapassar 100%")
    payload = data.model_dump(exclude={"product_ids"})
    p = Promotion(store_id=store_id, **payload)
    db.add(p); db.flush(); _sync_promotion_items(db, p, store_id, data.product_ids); db.commit(); db.refresh(p)
    return promotion_dict(db, p)


@admin_router.put("/promotions/{promotion_id}")
def update_promotion(promotion_id: int, data: PromotionUpdate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "promotions")
    p = db.query(Promotion).filter(Promotion.id == promotion_id, Promotion.store_id == store_id).first()
    if not p: raise HTTPException(status_code=404, detail="Promoção não encontrada")
    if data.discount_type == "PERCENT" and data.value > 100: raise HTTPException(status_code=400, detail="Percentual não pode ultrapassar 100%")
    for k, v in data.model_dump(exclude={"product_ids"}).items(): setattr(p, k, v)
    _sync_promotion_items(db, p, store_id, data.product_ids); db.commit(); db.refresh(p); return promotion_dict(db, p)


@admin_router.delete("/promotions/{promotion_id}")
def deactivate_promotion(promotion_id: int, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "promotions")
    p = db.query(Promotion).filter(Promotion.id == promotion_id, Promotion.store_id == store_id).first()
    if not p: raise HTTPException(status_code=404, detail="Promoção não encontrada")
    p.is_active = False; db.commit(); return {"ok": True}
