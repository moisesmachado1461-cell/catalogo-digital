import secrets
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from ..models.catalog import Product, ProductOption
from ..models.marketing import CouponUsage
from ..models.sales import Customer, Inventory, Order, OrderItem
from ..models.store import Store
from ..schemas.orders import CheckoutRequest
from .marketing_service import best_promotion_for_product, validate_coupon
from .payment_service import cancel_reference_payment, create_payment
from .subscription_service import feature_enabled

CENT = Decimal("0.01")

ALLOWED_TRANSITIONS = {
    "PENDENTE": {"CONFIRMADO", "CANCELADO"},
    "CONFIRMADO": {"EM_PREPARACAO", "CANCELADO"},
    "EM_PREPARACAO": {"PRONTO", "CANCELADO"},
    "PRONTO": {"SAIU_PARA_ENTREGA", "ENTREGUE", "CANCELADO"},
    "SAIU_PARA_ENTREGA": {"ENTREGUE", "CANCELADO"},
    "ENTREGUE": set(),
    "CANCELADO": set(),
}


def _money(value) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _order_number(store_id: int) -> str:
    now = datetime.now(timezone.utc)
    return f"CD{store_id}-{now:%Y%m%d}-{secrets.token_hex(3).upper()}"


def _new_public_token(db: Session) -> str:
    for _ in range(5):
        token = secrets.token_urlsafe(18)
        exists = db.query(Order.id).filter(Order.public_token == token).first()
        if not exists:
            return token
    raise HTTPException(status_code=500, detail="Não foi possível gerar o link de acompanhamento do pedido")


def _find_or_create_customer(db: Session, store_id: int, data) -> Customer:
    customer = None
    if data.email:
        customer = db.query(Customer).filter(Customer.store_id == store_id, Customer.email == str(data.email).lower()).first()
    if not customer and data.phone:
        customer = db.query(Customer).filter(Customer.store_id == store_id, Customer.phone == data.phone.strip()).first()
    if not customer:
        customer = Customer(
            store_id=store_id,
            name=data.name.strip(),
            email=(str(data.email).lower() if data.email else None),
            phone=(data.phone.strip() if data.phone else None),
            is_active=True,
        )
        db.add(customer)
        db.flush()
    else:
        customer.name = data.name.strip()
        if data.email: customer.email = str(data.email).lower()
        if data.phone: customer.phone = data.phone.strip()
    return customer


def _selected_options_for_product(product: Product, selected_ids: list[int]):
    selected_set = set(selected_ids or [])
    if len(selected_set) != len(selected_ids or []):
        raise HTTPException(status_code=400, detail=f"Há adicionais repetidos em {product.name}")

    known_item_ids = {item.id for option in product.options if option.is_active for item in option.items if item.is_active}
    if not selected_set.issubset(known_item_ids):
        raise HTTPException(status_code=400, detail=f"Há adicionais inválidos para {product.name}")

    snapshots = []
    extra = Decimal("0.00")
    for option in [o for o in product.options if o.is_active]:
        chosen = [item for item in option.items if item.is_active and item.id in selected_set]
        minimum = option.min_selections
        if option.required:
            minimum = max(1, minimum)
        if len(chosen) < minimum:
            raise HTTPException(status_code=400, detail=f"Selecione pelo menos {minimum} opção(ões) em {option.name}")
        if len(chosen) > option.max_selections:
            raise HTTPException(status_code=400, detail=f"Selecione no máximo {option.max_selections} opção(ões) em {option.name}")
        for item in chosen:
            adjustment = _money(item.price_adjustment)
            extra += adjustment
            snapshots.append({"option_id": option.id, "option_name": option.name, "item_id": item.id, "item_name": item.name, "price_adjustment": str(adjustment)})
    return snapshots, _money(extra)


def create_order_for_store(db: Session, store: Store, data: CheckoutRequest) -> Order:
    if not store.is_active:
        raise HTTPException(status_code=404, detail="Loja indisponível")
    if not store.capabilities.get("checkout", False):
        raise HTTPException(status_code=403, detail="Checkout não está habilitado para esta loja")
    if data.fulfillment_method == "ENTREGA" and not data.delivery_address:
        raise HTTPException(status_code=400, detail="Endereço é obrigatório para entrega")

    customer = _find_or_create_customer(db, store.id, data.customer)
    subtotal = Decimal("0.00")
    prepared_items = []

    for requested in data.items:
        product = (
            db.query(Product)
            .options(selectinload(Product.variants), selectinload(Product.options).selectinload(ProductOption.items))
            .filter(Product.id == requested.product_id, Product.store_id == store.id, Product.is_active.is_(True))
            .first()
        )
        if not product:
            raise HTTPException(status_code=400, detail=f"Produto {requested.product_id} não está disponível nesta loja")

        variant = None
        if product.variants and requested.variant_id is None:
            raise HTTPException(status_code=400, detail=f"Escolha uma variante para {product.name}")
        if requested.variant_id is not None:
            variant = next((v for v in product.variants if v.id == requested.variant_id and v.store_id == store.id and v.is_active), None)
            if not variant:
                raise HTTPException(status_code=400, detail="Variante inválida para este produto")

        base_price = _money(variant.price if variant and variant.price is not None else product.price)
        selected_options, options_total = _selected_options_for_product(product, requested.selected_option_item_ids)

        promotion = None
        promotion_discount = Decimal("0.00")
        if store.capabilities.get("promotions", False) and feature_enabled(db, store.id, "promotions"):
            promotion, promotion_discount = best_promotion_for_product(db, store.id, product.id, base_price)
        promotional_base = _money(base_price - promotion_discount)
        unit_price = _money(promotional_base + options_total)
        line_total = _money(unit_price * requested.quantity)
        subtotal += line_total

        inventory = None
        if product.track_inventory:
            query = db.query(Inventory).filter(Inventory.store_id == store.id, Inventory.product_id == product.id)
            query = query.filter(Inventory.variant_id == variant.id) if variant else query.filter(Inventory.variant_id.is_(None))
            inventory = query.first()
            if not inventory:
                raise HTTPException(status_code=409, detail=f"Estoque não configurado para {product.name}")
            available = inventory.quantity - inventory.reserved_quantity
            if available < requested.quantity:
                raise HTTPException(status_code=409, detail=f"Estoque insuficiente para {product.name}")

        prepared_items.append((product, variant, inventory, requested.quantity, base_price + options_total, unit_price, promotion.name if promotion else None, selected_options))

    subtotal = _money(subtotal)
    product_line_totals: dict[int, Decimal] = {}
    for product, _variant, _inventory, quantity, _original_unit_price, unit_price, _promotion_name, _selected_options in prepared_items:
        product_line_totals[product.id] = _money(
            product_line_totals.get(product.id, Decimal("0.00")) + (_money(unit_price) * quantity)
        )

    coupon = None
    discount = Decimal("0.00")
    if data.coupon_code:
        if not store.capabilities.get("coupons", False) or not feature_enabled(db, store.id, "coupons"):
            raise HTTPException(status_code=403, detail="Cupons não estão disponíveis para esta loja ou plano")
        coupon, discount = validate_coupon(
            db, store.id, data.coupon_code, subtotal, product_line_totals=product_line_totals
        )

    delivery_fee = Decimal("0.00")
    total = _money(max(Decimal("0.00"), subtotal - discount + delivery_fee))

    order = Order(
        store_id=store.id,
        customer_id=customer.id,
        public_token=_new_public_token(db),
        order_number=_order_number(store.id),
        status="PENDENTE",
        payment_method=data.payment_method,
        fulfillment_method=data.fulfillment_method,
        subtotal=subtotal,
        discount_amount=discount,
        coupon_code=(coupon.code if coupon else None),
        delivery_fee=delivery_fee,
        total=total,
        notes=data.notes,
        delivery_address=data.delivery_address,
        delivery_city=data.delivery_city,
        delivery_state=(data.delivery_state.upper() if data.delivery_state else None),
        delivery_zip_code=data.delivery_zip_code,
    )
    db.add(order); db.flush()

    for product, variant, inventory, quantity, original_unit_price, unit_price, promotion_name, selected_options in prepared_items:
        db.add(OrderItem(
            store_id=store.id,
            order_id=order.id,
            product_id=product.id,
            variant_id=variant.id if variant else None,
            product_name=product.name,
            variant_name=variant.name if variant else None,
            sku=(variant.sku if variant else product.sku),
            original_unit_price=_money(original_unit_price),
            unit_price=unit_price,
            promotion_name=promotion_name,
            selected_options=selected_options,
            quantity=quantity,
            line_total=_money(unit_price * quantity),
        ))
        if inventory:
            inventory.quantity -= quantity

    if coupon:
        coupon.usage_count += 1
        db.add(CouponUsage(store_id=store.id, coupon_id=coupon.id, order_id=order.id, customer_id=customer.id, discount_amount=discount))

    create_payment(
        db,
        store,
        reference_type="ORDER",
        reference_id=order.id,
        amount=order.total,
        method=data.payment_method,
    )

    db.commit(); db.refresh(order)
    return order


def update_order_status(db: Session, order: Order, new_status: str) -> Order:
    if new_status == order.status:
        return order
    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise HTTPException(status_code=409, detail=f"Transição de {order.status} para {new_status} não permitida")

    if new_status == "CANCELADO":
        cancel_reference_payment(db, order.store_id, "ORDER", order.id)
        for item in order.items:
            if item.product_id is None:
                continue
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product or not product.track_inventory:
                continue
            query = db.query(Inventory).filter(Inventory.store_id == order.store_id, Inventory.product_id == item.product_id)
            query = query.filter(Inventory.variant_id == item.variant_id) if item.variant_id is not None else query.filter(Inventory.variant_id.is_(None))
            inventory = query.first()
            if inventory:
                inventory.quantity += item.quantity

    order.status = new_status
    db.commit(); db.refresh(order)
    return order
