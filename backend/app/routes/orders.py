from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.sales import Order
from ..repositories.catalog_repository import get_store_by_slug
from ..schemas.orders import CheckoutRequest, OrderStatusUpdate
from ..services.order_service import create_order_for_store, update_order_status
from ..services.payment_service import payment_dict, payment_for_reference

public_router = APIRouter(prefix="/api/public", tags=["orders-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["orders-admin"])


def _order_dict(order: Order, payment=None):
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_method": order.payment_method,
        "fulfillment_method": order.fulfillment_method,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount,
        "coupon_code": order.coupon_code,
        "delivery_fee": order.delivery_fee,
        "total": order.total,
        "notes": order.notes,
        "customer": (
            {
                "id": order.customer.id,
                "name": order.customer.name,
                "email": order.customer.email,
                "phone": order.customer.phone,
            }
            if order.customer
            else None
        ),
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "product_name": item.product_name,
                "variant_name": item.variant_name,
                "sku": item.sku,
                "original_unit_price": item.original_unit_price,
                "unit_price": item.unit_price,
                "promotion_name": item.promotion_name,
                "selected_options": item.selected_options or [],
                "quantity": item.quantity,
                "line_total": item.line_total,
            }
            for item in order.items
        ],
        "created_at": order.created_at.isoformat(),
        "payment": payment_dict(payment),
    }


@public_router.post("/stores/{slug}/orders", status_code=201)
def checkout(slug: str, data: CheckoutRequest, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    order = create_order_for_store(db, store, data)
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.customer))
        .filter(Order.id == order.id, Order.store_id == store.id)
        .one()
    )
    return _order_dict(order, payment_for_reference(db, store.id, "ORDER", order.id))


@admin_router.get("/orders")
def list_orders(
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.customer))
        .filter(Order.store_id == store_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [_order_dict(order, payment_for_reference(db, store_id, "ORDER", order.id)) for order in orders]


@admin_router.get("/orders/{order_id}")
def get_order(
    order_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.customer))
        .filter(Order.id == order_id, Order.store_id == store_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return _order_dict(order, payment_for_reference(db, store_id, "ORDER", order.id))


@admin_router.patch("/orders/{order_id}/status")
def change_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.customer))
        .filter(Order.id == order_id, Order.store_id == store_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    update_order_status(db, order, data.status)
    return _order_dict(order, payment_for_reference(db, store_id, "ORDER", order.id))
