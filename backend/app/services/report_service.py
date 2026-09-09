from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session, selectinload

from ..models.payments import Payment
from ..models.quotes import QuoteRequest
from ..models.reservations import RentalReservation, Reservation
from ..models.sales import Customer, Inventory, Order
from ..models.services import Appointment


def _cutoff(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=max(1, days))


def _money(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"))


def _day_key(value: datetime) -> str:
    if value.tzinfo is None:
        return value.date().isoformat()
    return value.astimezone(timezone.utc).date().isoformat()


def report_overview(db: Session, store_id: int, days: int = 30) -> dict:
    cutoff = _cutoff(days)
    orders = db.query(Order).filter(Order.store_id == store_id, Order.created_at >= cutoff).all()
    active_orders = [row for row in orders if row.status != "CANCELADO"]
    order_revenue = sum((_money(row.total) for row in active_orders), Decimal("0.00"))

    appointments = db.query(Appointment).filter(Appointment.store_id == store_id, Appointment.created_at >= cutoff).all()
    quotes = db.query(QuoteRequest).filter(QuoteRequest.store_id == store_id, QuoteRequest.created_at >= cutoff).all()
    reservations = db.query(Reservation).filter(Reservation.store_id == store_id, Reservation.created_at >= cutoff).all()
    rentals = db.query(RentalReservation).filter(RentalReservation.store_id == store_id, RentalReservation.created_at >= cutoff).all()
    payments = db.query(Payment).filter(Payment.store_id == store_id, Payment.created_at >= cutoff).all()

    paid = [row for row in payments if row.status == "PAGO"]
    pending = [row for row in payments if row.status == "PENDENTE"]
    reservation_revenue = sum((_money(row.total) for row in reservations if row.status != "CANCELADA"), Decimal("0.00"))
    rental_revenue = sum((_money(row.total) for row in rentals if row.status != "CANCELADA"), Decimal("0.00"))

    low_stock = (
        db.query(Inventory)
        .filter(Inventory.store_id == store_id, Inventory.quantity <= Inventory.min_quantity)
        .count()
    )
    new_customers = db.query(Customer).filter(Customer.store_id == store_id, Customer.created_at >= cutoff).count()

    return {
        "period_days": days,
        "orders": {
            "count": len(orders),
            "active_count": len(active_orders),
            "revenue": str(order_revenue),
            "average_ticket": str((order_revenue / len(active_orders)).quantize(Decimal("0.01")) if active_orders else Decimal("0.00")),
            "pending": sum(1 for row in orders if row.status == "PENDENTE"),
            "cancelled": sum(1 for row in orders if row.status == "CANCELADO"),
        },
        "customers": {"new": new_customers},
        "appointments": {
            "count": len(appointments),
            "completed": sum(1 for row in appointments if row.status == "CONCLUIDO"),
            "pending": sum(1 for row in appointments if row.status in {"PENDENTE", "CONFIRMADO"}),
            "cancelled": sum(1 for row in appointments if row.status == "CANCELADO"),
        },
        "quotes": {
            "count": len(quotes),
            "approved": sum(1 for row in quotes if row.status in {"APROVADO", "CONCLUIDO"}),
            "pending": sum(1 for row in quotes if row.status in {"RECEBIDO", "EM_ANALISE", "ORCAMENTO_ENVIADO"}),
        },
        "reservations": {
            "count": len(reservations),
            "revenue": str(reservation_revenue),
            "pending": sum(1 for row in reservations if row.status in {"PENDENTE", "CONFIRMADA"}),
        },
        "rentals": {
            "count": len(rentals),
            "revenue": str(rental_revenue),
            "pending": sum(1 for row in rentals if row.status in {"PENDENTE", "CONFIRMADA", "RETIRADA"}),
        },
        "payments": {
            "paid_count": len(paid),
            "paid_total": str(sum((_money(row.amount) for row in paid), Decimal("0.00"))),
            "pending_count": len(pending),
            "pending_total": str(sum((_money(row.amount) for row in pending), Decimal("0.00"))),
        },
        "inventory": {"low_stock_count": low_stock},
    }


def report_timeseries(db: Session, store_id: int, days: int = 30) -> list[dict]:
    cutoff = _cutoff(days)
    orders = db.query(Order).filter(Order.store_id == store_id, Order.created_at >= cutoff).all()
    appointments = db.query(Appointment).filter(Appointment.store_id == store_id, Appointment.created_at >= cutoff).all()
    payments = db.query(Payment).filter(Payment.store_id == store_id, Payment.created_at >= cutoff, Payment.status == "PAGO").all()

    rows = {}
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=max(1, days) - 1)
    for offset in range(max(1, days)):
        key = (start + timedelta(days=offset)).isoformat()
        rows[key] = {"date": key, "orders": 0, "order_revenue": Decimal("0.00"), "appointments": 0, "paid_total": Decimal("0.00")}

    for order in orders:
        key = _day_key(order.created_at)
        if key in rows:
            rows[key]["orders"] += 1
            if order.status != "CANCELADO":
                rows[key]["order_revenue"] += _money(order.total)
    for appointment in appointments:
        key = _day_key(appointment.created_at)
        if key in rows:
            rows[key]["appointments"] += 1
    for payment in payments:
        key = _day_key(payment.created_at)
        if key in rows:
            rows[key]["paid_total"] += _money(payment.amount)

    return [
        {
            **row,
            "order_revenue": str(row["order_revenue"].quantize(Decimal("0.01"))),
            "paid_total": str(row["paid_total"].quantize(Decimal("0.01"))),
        }
        for row in rows.values()
    ]


def report_top_items(db: Session, store_id: int, days: int = 30, limit: int = 10) -> dict:
    cutoff = _cutoff(days)
    orders = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.store_id == store_id, Order.created_at >= cutoff, Order.status != "CANCELADO")
        .all()
    )
    product_rows: dict[str, dict] = {}
    for order in orders:
        for item in order.items:
            key = f"{item.product_id or 'deleted'}:{item.variant_id or 0}:{item.product_name}:{item.variant_name or ''}"
            row = product_rows.setdefault(key, {
                "name": item.product_name + (f" · {item.variant_name}" if item.variant_name else ""),
                "quantity": 0,
                "revenue": Decimal("0.00"),
            })
            row["quantity"] += int(item.quantity or 0)
            row["revenue"] += _money(item.line_total)

    appointments = (
        db.query(Appointment)
        .options(selectinload(Appointment.service))
        .filter(Appointment.store_id == store_id, Appointment.created_at >= cutoff, Appointment.status != "CANCELADO")
        .all()
    )
    service_rows: dict[int, dict] = {}
    for appointment in appointments:
        service_id = appointment.service_id
        name = appointment.service.name if appointment.service else f"Serviço #{service_id}"
        row = service_rows.setdefault(service_id, {"name": name, "count": 0})
        row["count"] += 1

    products = sorted(product_rows.values(), key=lambda x: (x["quantity"], x["revenue"]), reverse=True)[:limit]
    services = sorted(service_rows.values(), key=lambda x: x["count"], reverse=True)[:limit]
    for row in products:
        row["revenue"] = str(row["revenue"].quantize(Decimal("0.01")))
    return {"products": products, "services": services}
