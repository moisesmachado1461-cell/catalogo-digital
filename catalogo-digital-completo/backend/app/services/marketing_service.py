from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.marketing import Coupon, CouponProduct, Promotion, PromotionItem

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _window_active(starts_at, ends_at) -> bool:
    now = datetime.now(timezone.utc)
    if starts_at:
        start = starts_at if starts_at.tzinfo else starts_at.replace(tzinfo=timezone.utc)
        if start > now:
            return False
    if ends_at:
        end = ends_at if ends_at.tzinfo else ends_at.replace(tzinfo=timezone.utc)
        if end < now:
            return False
    return True


def discount_value(discount_type: str, value: Decimal, amount: Decimal, max_discount: Decimal | None = None) -> Decimal:
    amount = money(amount)
    if discount_type == "PERCENT":
        if value > 100:
            raise HTTPException(status_code=400, detail="Percentual de desconto não pode ultrapassar 100%")
        discount = amount * (Decimal(value) / Decimal("100"))
    else:
        discount = Decimal(value)
    if max_discount is not None:
        discount = min(discount, Decimal(max_discount))
    return money(min(max(discount, Decimal("0")), amount))


def best_promotion_for_product(db: Session, store_id: int, product_id: int, base_price: Decimal):
    rows = (
        db.query(Promotion)
        .join(PromotionItem, PromotionItem.promotion_id == Promotion.id)
        .filter(
            Promotion.store_id == store_id,
            PromotionItem.store_id == store_id,
            PromotionItem.product_id == product_id,
            Promotion.is_active.is_(True),
        )
        .all()
    )
    best = None
    best_discount = Decimal("0.00")
    for promotion in rows:
        if not _window_active(promotion.starts_at, promotion.ends_at):
            continue
        try:
            amount = discount_value(promotion.discount_type, promotion.value, base_price)
        except HTTPException:
            continue
        if amount > best_discount:
            best = promotion
            best_discount = amount
    return best, money(best_discount)


def validate_coupon(
    db: Session,
    store_id: int,
    code: str | None,
    subtotal: Decimal,
    product_line_totals: dict[int, Decimal] | None = None,
):
    if not code:
        return None, Decimal("0.00")
    normalized = code.strip().upper().replace(" ", "")
    coupon = db.query(Coupon).filter(Coupon.store_id == store_id, Coupon.code == normalized).first()
    if not coupon or not coupon.is_active or not _window_active(coupon.starts_at, coupon.ends_at):
        raise HTTPException(status_code=400, detail="Cupom inválido ou expirado")
    if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Este cupom atingiu o limite de usos")
    if subtotal < coupon.min_order_value:
        raise HTTPException(status_code=400, detail=f"Pedido mínimo para este cupom: R$ {coupon.min_order_value}")

    product_ids = [
        row.product_id
        for row in db.query(CouponProduct).filter(
            CouponProduct.store_id == store_id, CouponProduct.coupon_id == coupon.id
        ).all()
    ]
    eligible_amount = money(subtotal)
    if product_ids:
        totals = product_line_totals or {}
        eligible_amount = money(sum((Decimal(totals.get(product_id, 0)) for product_id in product_ids), Decimal("0.00")))
        if eligible_amount <= 0:
            raise HTTPException(status_code=400, detail="Este cupom é válido apenas para produtos selecionados que não estão no carrinho")

    return coupon, discount_value(coupon.discount_type, coupon.value, eligible_amount, coupon.max_discount)


def active_promotions_for_store(db: Session, store_id: int):
    promotions = db.query(Promotion).filter(Promotion.store_id == store_id, Promotion.is_active.is_(True)).order_by(Promotion.id.desc()).all()
    result = []
    for promotion in promotions:
        if not _window_active(promotion.starts_at, promotion.ends_at):
            continue
        product_ids = [row.product_id for row in db.query(PromotionItem).filter(PromotionItem.promotion_id == promotion.id, PromotionItem.store_id == store_id).all()]
        result.append({
            "id": promotion.id,
            "name": promotion.name,
            "description": promotion.description,
            "discount_type": promotion.discount_type,
            "value": promotion.value,
            "product_ids": product_ids,
            "starts_at": promotion.starts_at.isoformat() if promotion.starts_at else None,
            "ends_at": promotion.ends_at.isoformat() if promotion.ends_at else None,
        })
    return result


def active_public_coupons_for_store(db: Session, store_id: int):
    coupons = (
        db.query(Coupon)
        .filter(
            Coupon.store_id == store_id,
            Coupon.is_active.is_(True),
            Coupon.is_public.is_(True),
        )
        .order_by(Coupon.created_at.desc(), Coupon.id.desc())
        .all()
    )
    result = []
    for coupon in coupons:
        if not _window_active(coupon.starts_at, coupon.ends_at):
            continue
        if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
            continue
        remaining = None if coupon.usage_limit is None else max(coupon.usage_limit - coupon.usage_count, 0)
        product_ids = [
            row.product_id
            for row in db.query(CouponProduct).filter(
                CouponProduct.store_id == store_id, CouponProduct.coupon_id == coupon.id
            ).all()
        ]
        result.append({
            "id": coupon.id,
            "code": coupon.code,
            "description": coupon.description,
            "discount_type": coupon.discount_type,
            "value": coupon.value,
            "min_order_value": coupon.min_order_value,
            "max_discount": coupon.max_discount,
            "starts_at": coupon.starts_at.isoformat() if coupon.starts_at else None,
            "ends_at": coupon.ends_at.isoformat() if coupon.ends_at else None,
            "usage_remaining": remaining,
            "product_ids": product_ids,
            "scope": "PRODUCTS" if product_ids else "ORDER",
        })
    return result
