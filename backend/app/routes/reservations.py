from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.reservations import Resource, Reservation, RentalItem, RentalReservation
from ..models.store import Store
from ..repositories.catalog_repository import get_store_by_slug
from ..schemas.reservations import ResourceCreate, ResourceUpdate, ReservationCreate, ReservationStatusUpdate, RentalItemCreate, RentalItemUpdate, RentalCreate, RentalStatusUpdate
from ..services.reservation_service import RESERVATION_TRANSITIONS, RENTAL_TRANSITIONS, create_reservation, create_rental, rental_availability, require_capability, update_status
from ..services.payment_service import cancel_reference_payment, payment_dict, payment_for_reference
from ..utils.text import slugify

public_router = APIRouter(prefix="/api/public", tags=["reservations-rentals-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["reservations-rentals-admin"])


def _iso(value):
    if value is None: return None
    if value.tzinfo is None: value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _resource_dict(x):
    return {"id": x.id, "name": x.name, "slug": x.slug, "description": x.description, "resource_type": x.resource_type, "capacity": x.capacity, "price_per_day": str(x.price_per_day), "image_url": x.image_url, "is_active": x.is_active}


def _reservation_dict(x, payment=None):
    return {"id": x.id, "public_token": x.public_token, "resource_id": x.resource_id, "resource": _resource_dict(x.resource) if x.resource else None, "customer": {"id": x.customer.id, "name": x.customer.name, "email": x.customer.email, "phone": x.customer.phone} if x.customer else None, "starts_at": _iso(x.starts_at), "ends_at": _iso(x.ends_at), "guests": x.guests, "status": x.status, "daily_rate_snapshot": str(x.daily_rate_snapshot), "total": str(x.total), "notes": x.notes, "created_at": _iso(x.created_at), "payment": payment_dict(payment)}


def _rental_item_dict(x):
    return {"id": x.id, "name": x.name, "slug": x.slug, "description": x.description, "sku": x.sku, "daily_rate": str(x.daily_rate), "deposit_amount": str(x.deposit_amount), "quantity_total": x.quantity_total, "image_url": x.image_url, "is_active": x.is_active}


def _rental_dict(x, payment=None):
    return {"id": x.id, "public_token": x.public_token, "rental_item_id": x.rental_item_id, "item": _rental_item_dict(x.item) if x.item else None, "customer": {"id": x.customer.id, "name": x.customer.name, "email": x.customer.email, "phone": x.customer.phone} if x.customer else None, "starts_at": _iso(x.starts_at), "ends_at": _iso(x.ends_at), "quantity": x.quantity, "rental_days": x.rental_days, "daily_rate_snapshot": str(x.daily_rate_snapshot), "deposit_amount": str(x.deposit_amount), "total": str(x.total), "status": x.status, "notes": x.notes, "created_at": _iso(x.created_at), "payment": payment_dict(payment)}


def _admin_store(db, store_id):
    store = db.query(Store).filter(Store.id == store_id, Store.is_active.is_(True)).first()
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    return store


def _commit(db, conflict):
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail=conflict)


@public_router.get("/stores/{slug}/resources")
def public_resources(slug: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    require_capability(store, "reservations")
    rows = db.query(Resource).filter(Resource.store_id == store.id, Resource.is_active.is_(True)).order_by(Resource.name).all()
    return {"store": {"id": store.id, "name": store.name, "slug": store.slug}, "resources": [_resource_dict(x) for x in rows]}


@public_router.post("/stores/{slug}/reservations", status_code=201)
def public_create_reservation(slug: str, data: ReservationCreate, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    row = create_reservation(db, store, data)
    row = db.query(Reservation).options(selectinload(Reservation.resource), selectinload(Reservation.customer)).filter(Reservation.id == row.id).one()
    return _reservation_dict(row, payment_for_reference(db, store.id, "RESERVATION", row.id))


@public_router.get("/stores/{slug}/reservations/{token}")
def public_get_reservation(slug: str, token: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    row = db.query(Reservation).options(selectinload(Reservation.resource), selectinload(Reservation.customer)).filter(Reservation.store_id == store.id, Reservation.public_token == token).first()
    if not row: raise HTTPException(status_code=404, detail="Reserva não encontrada")
    return _reservation_dict(row, payment_for_reference(db, store.id, "RESERVATION", row.id))


@public_router.patch("/stores/{slug}/reservations/{token}/cancel")
def public_cancel_reservation(slug: str, token: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    row = db.query(Reservation).options(selectinload(Reservation.resource), selectinload(Reservation.customer)).filter(Reservation.store_id == store.id, Reservation.public_token == token).first()
    if not row: raise HTTPException(status_code=404, detail="Reserva não encontrada")
    if row.status not in {"PENDENTE", "CONFIRMADA"}: raise HTTPException(status_code=409, detail="Esta reserva não pode mais ser cancelada")
    row.status = "CANCELADA"; cancel_reference_payment(db, store.id, "RESERVATION", row.id); db.commit(); db.refresh(row); return _reservation_dict(row, payment_for_reference(db, store.id, "RESERVATION", row.id))


@public_router.get("/stores/{slug}/rental-items")
def public_rental_items(slug: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    require_capability(store, "rentals")
    rows = db.query(RentalItem).filter(RentalItem.store_id == store.id, RentalItem.is_active.is_(True)).order_by(RentalItem.name).all()
    return {"store": {"id": store.id, "name": store.name, "slug": store.slug}, "items": [_rental_item_dict(x) for x in rows]}


@public_router.get("/stores/{slug}/rentals/availability")
def public_rental_availability(slug: str, item_id: int, starts_at: datetime, ends_at: datetime, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    return rental_availability(db, store, item_id, starts_at, ends_at)


@public_router.post("/stores/{slug}/rentals", status_code=201)
def public_create_rental(slug: str, data: RentalCreate, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    row = create_rental(db, store, data)
    row = db.query(RentalReservation).options(selectinload(RentalReservation.item), selectinload(RentalReservation.customer)).filter(RentalReservation.id == row.id).one()
    return _rental_dict(row, payment_for_reference(db, store.id, "RENTAL", row.id))


@public_router.get("/stores/{slug}/rentals/{token}")
def public_get_rental(slug: str, token: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    row = db.query(RentalReservation).options(selectinload(RentalReservation.item), selectinload(RentalReservation.customer)).filter(RentalReservation.store_id == store.id, RentalReservation.public_token == token).first()
    if not row: raise HTTPException(status_code=404, detail="Locação não encontrada")
    return _rental_dict(row, payment_for_reference(db, store.id, "RENTAL", row.id))


@public_router.patch("/stores/{slug}/rentals/{token}/cancel")
def public_cancel_rental(slug: str, token: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store: raise HTTPException(status_code=404, detail="Loja não encontrada")
    row = db.query(RentalReservation).options(selectinload(RentalReservation.item), selectinload(RentalReservation.customer)).filter(RentalReservation.store_id == store.id, RentalReservation.public_token == token).first()
    if not row: raise HTTPException(status_code=404, detail="Locação não encontrada")
    if row.status not in {"PENDENTE", "CONFIRMADA"}: raise HTTPException(status_code=409, detail="Esta locação não pode mais ser cancelada")
    row.status = "CANCELADA"; cancel_reference_payment(db, store.id, "RENTAL", row.id); db.commit(); db.refresh(row); return _rental_dict(row, payment_for_reference(db, store.id, "RENTAL", row.id))


@admin_router.get("/resources")
def admin_resources(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "reservations")
    return [_resource_dict(x) for x in db.query(Resource).filter(Resource.store_id == store_id).order_by(Resource.name).all()]


@admin_router.post("/resources", status_code=201)
def admin_create_resource(data: ResourceCreate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "reservations")
    row = Resource(store_id=store_id, name=data.name.strip(), slug=slugify(data.slug or data.name), description=data.description, resource_type=data.resource_type.strip().upper(), capacity=data.capacity, price_per_day=data.price_per_day, image_url=data.image_url, is_active=True)
    db.add(row); _commit(db, "Já existe um recurso com esse slug nesta loja"); db.refresh(row); return _resource_dict(row)


@admin_router.put("/resources/{resource_id}")
def admin_update_resource(resource_id: int, data: ResourceUpdate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "reservations")
    row = db.query(Resource).filter(Resource.id == resource_id, Resource.store_id == store_id).first()
    if not row: raise HTTPException(status_code=404, detail="Recurso não encontrado")
    values = data.model_dump(exclude_unset=True)
    if values.get("name") is not None: values["name"] = values["name"].strip()
    if values.get("slug") is not None: values["slug"] = slugify(values["slug"])
    if values.get("resource_type") is not None: values["resource_type"] = values["resource_type"].strip().upper()
    for k, v in values.items(): setattr(row, k, v)
    _commit(db, "Já existe um recurso com esse slug nesta loja"); db.refresh(row); return _resource_dict(row)


@admin_router.get("/reservations")
def admin_reservations(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "reservations")
    rows = db.query(Reservation).options(selectinload(Reservation.resource), selectinload(Reservation.customer)).filter(Reservation.store_id == store_id).order_by(Reservation.starts_at.desc()).all()
    return [_reservation_dict(x, payment_for_reference(db, store_id, "RESERVATION", x.id)) for x in rows]


@admin_router.patch("/reservations/{reservation_id}/status")
def admin_reservation_status(reservation_id: int, data: ReservationStatusUpdate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "reservations")
    row = db.query(Reservation).options(selectinload(Reservation.resource), selectinload(Reservation.customer)).filter(Reservation.id == reservation_id, Reservation.store_id == store_id).first()
    if not row: raise HTTPException(status_code=404, detail="Reserva não encontrada")
    update_status(db, row, data.status, RESERVATION_TRANSITIONS); return _reservation_dict(row, payment_for_reference(db, store_id, "RESERVATION", row.id))


@admin_router.get("/rental-items")
def admin_rental_items(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "rentals")
    return [_rental_item_dict(x) for x in db.query(RentalItem).filter(RentalItem.store_id == store_id).order_by(RentalItem.name).all()]


@admin_router.post("/rental-items", status_code=201)
def admin_create_rental_item(data: RentalItemCreate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "rentals")
    row = RentalItem(store_id=store_id, name=data.name.strip(), slug=slugify(data.slug or data.name), description=data.description, sku=data.sku.strip() if data.sku else None, daily_rate=data.daily_rate, deposit_amount=data.deposit_amount, quantity_total=data.quantity_total, image_url=data.image_url, is_active=True)
    db.add(row); _commit(db, "Slug ou SKU já usado nesta loja"); db.refresh(row); return _rental_item_dict(row)


@admin_router.put("/rental-items/{item_id}")
def admin_update_rental_item(item_id: int, data: RentalItemUpdate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "rentals")
    row = db.query(RentalItem).filter(RentalItem.id == item_id, RentalItem.store_id == store_id).first()
    if not row: raise HTTPException(status_code=404, detail="Item não encontrado")
    values = data.model_dump(exclude_unset=True)
    if values.get("name") is not None: values["name"] = values["name"].strip()
    if values.get("slug") is not None: values["slug"] = slugify(values["slug"])
    if "sku" in values: values["sku"] = values["sku"].strip() if values["sku"] else None
    for k, v in values.items(): setattr(row, k, v)
    _commit(db, "Slug ou SKU já usado nesta loja"); db.refresh(row); return _rental_item_dict(row)


@admin_router.get("/rentals")
def admin_rentals(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "rentals")
    rows = db.query(RentalReservation).options(selectinload(RentalReservation.item), selectinload(RentalReservation.customer)).filter(RentalReservation.store_id == store_id).order_by(RentalReservation.starts_at.desc()).all()
    return [_rental_dict(x, payment_for_reference(db, store_id, "RENTAL", x.id)) for x in rows]


@admin_router.patch("/rentals/{rental_id}/status")
def admin_rental_status(rental_id: int, data: RentalStatusUpdate, store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_capability(_admin_store(db, store_id), "rentals")
    row = db.query(RentalReservation).options(selectinload(RentalReservation.item), selectinload(RentalReservation.customer)).filter(RentalReservation.id == rental_id, RentalReservation.store_id == store_id).first()
    if not row: raise HTTPException(status_code=404, detail="Locação não encontrada")
    update_status(db, row, data.status, RENTAL_TRANSITIONS); return _rental_dict(row, payment_for_reference(db, store_id, "RENTAL", row.id))
