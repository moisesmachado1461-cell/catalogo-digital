from datetime import datetime, timezone
from decimal import Decimal
import math
import secrets
from .payment_service import cancel_reference_payment, create_payment

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.reservations import Resource, Reservation, RentalItem, RentalReservation
from ..models.sales import Customer
from ..models.store import Store
from ..schemas.reservations import ReservationCreate, RentalCreate

RESERVATION_ACTIVE = {"PENDENTE", "CONFIRMADA"}
RENTAL_ACTIVE = {"PENDENTE", "CONFIRMADA", "RETIRADA"}
RESERVATION_TRANSITIONS = {
    "PENDENTE": {"CONFIRMADA", "CANCELADA"},
    "CONFIRMADA": {"CONCLUIDA", "CANCELADA"},
    "CONCLUIDA": set(),
    "CANCELADA": set(),
}
RENTAL_TRANSITIONS = {
    "PENDENTE": {"CONFIRMADA", "CANCELADA"},
    "CONFIRMADA": {"RETIRADA", "CANCELADA"},
    "RETIRADA": {"DEVOLVIDA"},
    "DEVOLVIDA": set(),
    "CANCELADA": set(),
}


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise HTTPException(status_code=400, detail="Data/hora deve incluir fuso horário")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _find_or_create_customer(db: Session, store_id: int, data) -> Customer:
    customer = None
    if data.email:
        customer = db.query(Customer).filter(Customer.store_id == store_id, Customer.email == str(data.email).lower()).first()
    if not customer and data.phone:
        customer = db.query(Customer).filter(Customer.store_id == store_id, Customer.phone == data.phone.strip()).first()
    if not customer:
        customer = Customer(store_id=store_id, name=data.name.strip(), email=str(data.email).lower() if data.email else None, phone=data.phone.strip() if data.phone else None, is_active=True)
        db.add(customer); db.flush()
    else:
        customer.name = data.name.strip()
        if data.email: customer.email = str(data.email).lower()
        if data.phone: customer.phone = data.phone.strip()
    return customer


def _token(db: Session, model) -> str:
    for _ in range(8):
        token = secrets.token_urlsafe(18)
        if not db.query(model.id).filter(model.public_token == token).first():
            return token
    raise HTTPException(status_code=500, detail="Não foi possível gerar protocolo")


def _days(start: datetime, end: datetime) -> int:
    seconds = (end - start).total_seconds()
    return max(1, math.ceil(seconds / 86400))


def require_capability(store: Store, capability: str) -> None:
    if not store.is_active:
        raise HTTPException(status_code=404, detail="Loja indisponível")
    if not store.capabilities.get(capability, False):
        raise HTTPException(status_code=403, detail=f"Capability '{capability}' não habilitada para esta loja")


def reservation_conflict(db: Session, store_id: int, resource_id: int, starts_at: datetime, ends_at: datetime, ignore_id: int | None = None) -> bool:
    query = db.query(Reservation).filter(
        Reservation.store_id == store_id,
        Reservation.resource_id == resource_id,
        Reservation.status.in_(RESERVATION_ACTIVE),
        Reservation.starts_at < ends_at,
        Reservation.ends_at > starts_at,
    )
    if ignore_id is not None: query = query.filter(Reservation.id != ignore_id)
    return query.first() is not None


def create_reservation(db: Session, store: Store, data: ReservationCreate) -> Reservation:
    require_capability(store, "reservations")
    resource = db.query(Resource).filter(Resource.id == data.resource_id, Resource.store_id == store.id, Resource.is_active.is_(True)).first()
    if not resource: raise HTTPException(status_code=404, detail="Recurso não encontrado")
    if data.guests > resource.capacity: raise HTTPException(status_code=409, detail=f"Capacidade máxima: {resource.capacity}")
    start = _to_utc_naive(data.starts_at); end = _to_utc_naive(data.ends_at)
    if start < datetime.now(timezone.utc).replace(tzinfo=None): raise HTTPException(status_code=409, detail="Não é possível reservar um período no passado")
    if reservation_conflict(db, store.id, resource.id, start, end): raise HTTPException(status_code=409, detail="Este recurso já está reservado nesse período")
    customer = _find_or_create_customer(db, store.id, data.customer)
    days = _days(start, end)
    total = (Decimal(resource.price_per_day) * Decimal(days)).quantize(Decimal("0.01"))
    row = Reservation(public_token=_token(db, Reservation), store_id=store.id, customer_id=customer.id, resource_id=resource.id, starts_at=start, ends_at=end, guests=data.guests, status="PENDENTE", daily_rate_snapshot=resource.price_per_day, total=total, notes=data.notes)
    db.add(row); db.flush()
    create_payment(db, store, reference_type="RESERVATION", reference_id=row.id, amount=total, method=data.payment_method)
    db.commit(); db.refresh(row); return row


def rental_reserved_quantity(db: Session, store_id: int, item_id: int, starts_at: datetime, ends_at: datetime, ignore_id: int | None = None) -> int:
    query = db.query(func.coalesce(func.sum(RentalReservation.quantity), 0)).filter(
        RentalReservation.store_id == store_id,
        RentalReservation.rental_item_id == item_id,
        RentalReservation.status.in_(RENTAL_ACTIVE),
        RentalReservation.starts_at < ends_at,
        RentalReservation.ends_at > starts_at,
    )
    if ignore_id is not None: query = query.filter(RentalReservation.id != ignore_id)
    return int(query.scalar() or 0)


def rental_availability(db: Session, store: Store, item_id: int, starts_at: datetime, ends_at: datetime) -> dict:
    require_capability(store, "rentals")
    item = db.query(RentalItem).filter(RentalItem.id == item_id, RentalItem.store_id == store.id, RentalItem.is_active.is_(True)).first()
    if not item: raise HTTPException(status_code=404, detail="Item de locação não encontrado")
    start = _to_utc_naive(starts_at); end = _to_utc_naive(ends_at)
    if end <= start: raise HTTPException(status_code=400, detail="Período inválido")
    reserved = rental_reserved_quantity(db, store.id, item.id, start, end)
    available = max(0, item.quantity_total - reserved)
    return {"item_id": item.id, "quantity_total": item.quantity_total, "reserved_quantity": reserved, "available_quantity": available, "rental_days": _days(start, end), "daily_rate": str(item.daily_rate), "deposit_amount": str(item.deposit_amount)}


def create_rental(db: Session, store: Store, data: RentalCreate) -> RentalReservation:
    require_capability(store, "rentals")
    item = db.query(RentalItem).filter(RentalItem.id == data.rental_item_id, RentalItem.store_id == store.id, RentalItem.is_active.is_(True)).first()
    if not item: raise HTTPException(status_code=404, detail="Item de locação não encontrado")
    start = _to_utc_naive(data.starts_at); end = _to_utc_naive(data.ends_at)
    if start < datetime.now(timezone.utc).replace(tzinfo=None): raise HTTPException(status_code=409, detail="Não é possível alugar em período passado")
    reserved = rental_reserved_quantity(db, store.id, item.id, start, end)
    available = item.quantity_total - reserved
    if data.quantity > available: raise HTTPException(status_code=409, detail=f"Quantidade disponível neste período: {max(0, available)}")
    customer = _find_or_create_customer(db, store.id, data.customer)
    days = _days(start, end)
    subtotal = Decimal(item.daily_rate) * Decimal(days) * Decimal(data.quantity)
    deposit = Decimal(item.deposit_amount) * Decimal(data.quantity)
    total = (subtotal + deposit).quantize(Decimal("0.01"))
    row = RentalReservation(public_token=_token(db, RentalReservation), store_id=store.id, customer_id=customer.id, rental_item_id=item.id, starts_at=start, ends_at=end, quantity=data.quantity, rental_days=days, daily_rate_snapshot=item.daily_rate, deposit_amount=deposit, total=total, status="PENDENTE", notes=data.notes)
    db.add(row); db.flush()
    create_payment(db, store, reference_type="RENTAL", reference_id=row.id, amount=total, method=data.payment_method)
    db.commit(); db.refresh(row); return row


def update_status(db: Session, row, new_status: str, transitions: dict):
    if new_status == row.status: return row
    if new_status not in transitions.get(row.status, set()):
        raise HTTPException(status_code=409, detail=f"Transição de {row.status} para {new_status} não permitida")
    row.status = new_status
    if new_status == "CANCELADA":
        reference_type = "RESERVATION" if isinstance(row, Reservation) else "RENTAL"
        cancel_reference_payment(db, row.store_id, reference_type, row.id)
    db.commit(); db.refresh(row); return row
