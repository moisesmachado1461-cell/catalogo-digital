from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.services import Appointment, Professional, ProfessionalBlock, ProfessionalHours, ProfessionalService, Service
from ..models.store import Store
from ..repositories.catalog_repository import get_store_by_slug
from ..schemas.services import (
    AppointmentCreate,
    AppointmentStatusUpdate,
    ProfessionalBlockCreate,
    ProfessionalCreate,
    ProfessionalHoursUpdate,
    ProfessionalServicesUpdate,
    ProfessionalUpdate,
    ServiceCreate,
    ServiceUpdate,
)
from ..services.appointment_service import (
    create_appointment,
    list_available_slots,
    update_appointment_status,
)
from ..services.payment_service import cancel_reference_payment, payment_dict, payment_for_reference
from ..services.subscription_service import enforce_limit
from ..services.service_service import (
    create_professional,
    create_service,
    get_professional_for_store,
    get_service_for_store,
    replace_professional_hours,
    replace_professional_services,
    update_professional,
    update_service,
)

public_router = APIRouter(prefix="/api/public", tags=["services-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["services-admin"])
appointments_admin_router = APIRouter(prefix="/api/admin", tags=["appointments-admin"])


def _require_capability(db: Session, store_id: int, capability: str) -> Store:
    store = db.query(Store).filter(Store.id == store_id, Store.is_active.is_(True)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    if not store.capabilities.get(capability, False):
        raise HTTPException(status_code=403, detail=f"Capability '{capability}' não habilitada para esta loja")
    return store


def _service_dict(service: Service):
    return {
        "id": service.id,
        "category_id": service.category_id,
        "name": service.name,
        "slug": service.slug,
        "description": service.description,
        "price": service.price,
        "duration_minutes": service.duration_minutes,
        "image_url": service.image_url,
        "is_active": service.is_active,
    }


def _professional_dict(professional: Professional):
    return {
        "id": professional.id,
        "name": professional.name,
        "description": professional.description,
        "phone": professional.phone,
        "email": professional.email,
        "image_url": professional.image_url,
        "is_active": professional.is_active,
        "service_ids": sorted(link.service_id for link in professional.service_links),
        "hours": [
            {
                "day_of_week": row.day_of_week,
                "start_time": row.start_time.isoformat(timespec="minutes"),
                "end_time": row.end_time.isoformat(timespec="minutes"),
                "is_active": row.is_active,
            }
            for row in sorted(professional.hours, key=lambda x: x.day_of_week)
        ],
    }


def _appointment_dict(appointment: Appointment, payment=None):
    def iso_utc(value):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.isoformat() + "Z"
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "id": appointment.id,
        "public_token": appointment.public_token,
        "store_id": appointment.store_id,
        "customer": (
            {
                "id": appointment.customer.id,
                "name": appointment.customer.name,
                "email": appointment.customer.email,
                "phone": appointment.customer.phone,
            }
            if appointment.customer
            else None
        ),
        "service": {
            "id": appointment.service.id,
            "name": appointment.service.name,
            "duration_minutes": appointment.service.duration_minutes,
            "price": appointment.service.price,
        },
        "professional": {
            "id": appointment.professional.id,
            "name": appointment.professional.name,
        },
        "starts_at": iso_utc(appointment.starts_at),
        "ends_at": iso_utc(appointment.ends_at),
        "status": appointment.status,
        "notes": appointment.notes,
        "can_cancel": appointment.status in {"PENDENTE", "CONFIRMADO"} and ((appointment.starts_at.replace(tzinfo=timezone.utc) if appointment.starts_at.tzinfo is None else appointment.starts_at.astimezone(timezone.utc)) > datetime.now(timezone.utc)),
        "payment": payment_dict(payment),
    }


@public_router.get("/stores/{slug}/services")
def public_services(slug: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    if not store.capabilities.get("services", False):
        raise HTTPException(status_code=404, detail="Serviços não habilitados para esta loja")

    services = (
        db.query(Service)
        .filter(Service.store_id == store.id, Service.is_active.is_(True))
        .order_by(Service.name)
        .all()
    )
    professionals = (
        db.query(Professional)
        .options(
            selectinload(Professional.service_links),
            selectinload(Professional.hours),
        )
        .filter(Professional.store_id == store.id, Professional.is_active.is_(True))
        .order_by(Professional.name)
        .all()
    )
    return {
        "store": {
            "id": store.id,
            "name": store.name,
            "slug": store.slug,
            "capabilities": store.capabilities,
            "primary_color": store.primary_color,
            "secondary_color": store.secondary_color,
        },
        "services": [_service_dict(item) for item in services],
        "professionals": [_professional_dict(item) for item in professionals],
    }


@public_router.get("/stores/{slug}/availability")
def public_availability(
    slug: str,
    service_id: int,
    professional_id: int,
    date_value: date = Query(alias="date"),
    utc_offset_minutes: int = Query(default=-180, ge=-720, le=840),
    slot_interval_minutes: int = Query(default=15, ge=5, le=120),
    db: Session = Depends(get_db),
):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    slots = list_available_slots(
        db,
        store,
        service_id,
        professional_id,
        date_value,
        utc_offset_minutes,
        slot_interval_minutes,
    )
    return {
        "store_id": store.id,
        "service_id": service_id,
        "professional_id": professional_id,
        "date": date_value.isoformat(),
        "utc_offset_minutes": utc_offset_minutes,
        "slots": slots,
    }


@public_router.post("/stores/{slug}/appointments", status_code=201)
def public_create_appointment(
    slug: str,
    data: AppointmentCreate,
    db: Session = Depends(get_db),
):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    appointment = create_appointment(db, store, data)
    appointment = (
        db.query(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
            selectinload(Appointment.professional),
        )
        .filter(Appointment.id == appointment.id)
        .one()
    )
    return _appointment_dict(appointment, payment_for_reference(db, store.id, "APPOINTMENT", appointment.id))


@public_router.get("/stores/{slug}/appointments/{public_token}")
def public_get_appointment(
    slug: str,
    public_token: str,
    db: Session = Depends(get_db),
):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    appointment = (
        db.query(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
            selectinload(Appointment.professional),
        )
        .filter(Appointment.store_id == store.id, Appointment.public_token == public_token)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    result = _appointment_dict(appointment, payment_for_reference(db, store.id, "APPOINTMENT", appointment.id))
    result["store"] = {"name": store.name, "slug": store.slug, "phone": store.phone, "whatsapp": store.whatsapp}
    return result


@public_router.patch("/stores/{slug}/appointments/{public_token}/cancel")
def public_cancel_appointment(
    slug: str,
    public_token: str,
    db: Session = Depends(get_db),
):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    appointment = (
        db.query(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
            selectinload(Appointment.professional),
        )
        .filter(Appointment.store_id == store.id, Appointment.public_token == public_token)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    if appointment.status not in {"PENDENTE", "CONFIRMADO"}:
        raise HTTPException(status_code=409, detail="Este agendamento não pode mais ser cancelado")
    appointment_start_utc = appointment.starts_at.replace(tzinfo=timezone.utc) if appointment.starts_at.tzinfo is None else appointment.starts_at.astimezone(timezone.utc)
    if appointment_start_utc <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="Não é possível cancelar um horário que já começou")
    appointment.status = "CANCELADO"
    cancel_reference_payment(db, store.id, "APPOINTMENT", appointment.id)
    db.commit()
    db.refresh(appointment)
    return _appointment_dict(appointment, payment_for_reference(db, store.id, "APPOINTMENT", appointment.id))


@admin_router.get("/appointment-blocks")
def list_admin_appointment_blocks(
    professional_id: int | None = Query(default=None),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    query = db.query(ProfessionalBlock).filter(ProfessionalBlock.store_id == store_id)
    if professional_id is not None:
        query = query.filter(ProfessionalBlock.professional_id == professional_id)
    rows = query.order_by(ProfessionalBlock.starts_at.desc()).all()
    return [{
        "id": row.id,
        "professional_id": row.professional_id,
        "starts_at": (row.starts_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if row.starts_at.tzinfo is None else row.starts_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")),
        "ends_at": (row.ends_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if row.ends_at.tzinfo is None else row.ends_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")),
        "reason": row.reason,
    } for row in rows]


@admin_router.post("/appointment-blocks", status_code=201)
def create_admin_appointment_block(
    data: ProfessionalBlockCreate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    professional = (
        db.query(Professional)
        .filter(Professional.id == data.professional_id, Professional.store_id == store_id, Professional.is_active.is_(True))
        .first()
    )
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    starts_at = data.starts_at.astimezone(timezone.utc).replace(tzinfo=None)
    ends_at = data.ends_at.astimezone(timezone.utc).replace(tzinfo=None)
    if ends_at <= starts_at:
        raise HTTPException(status_code=400, detail="Fim do bloqueio deve ser posterior ao início")
    block = ProfessionalBlock(
        store_id=store_id,
        professional_id=professional.id,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=data.reason.strip() if data.reason else None,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return {
        "id": block.id,
        "professional_id": block.professional_id,
        "starts_at": block.starts_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "ends_at": block.ends_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        "reason": block.reason,
    }


@admin_router.delete("/appointment-blocks/{block_id}")
def delete_admin_appointment_block(
    block_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    block = db.query(ProfessionalBlock).filter(ProfessionalBlock.id == block_id, ProfessionalBlock.store_id == store_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Bloqueio não encontrado")
    db.delete(block)
    db.commit()
    return {"ok": True}


@admin_router.get("/services")
def list_admin_services(
    include_inactive: bool = Query(default=True),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "services")
    query = db.query(Service).filter(Service.store_id == store_id)
    if not include_inactive:
        query = query.filter(Service.is_active.is_(True))
    return [_service_dict(item) for item in query.order_by(Service.name).all()]


@admin_router.post("/services", status_code=201)
def create_admin_service(
    data: ServiceCreate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "services")
    enforce_limit(db, store_id, "services")
    return _service_dict(create_service(db, store_id, data))


@admin_router.put("/services/{service_id}")
def update_admin_service(
    service_id: int,
    data: ServiceUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "services")
    current = get_service_for_store(db, store_id, service_id)
    if not current:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    if data.is_active is True and not current.is_active:
        enforce_limit(db, store_id, "services")
    return _service_dict(update_service(db, store_id, service_id, data))


@admin_router.delete("/services/{service_id}")
def deactivate_admin_service(
    service_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "services")
    service = get_service_for_store(db, store_id, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    service.is_active = False
    db.commit()
    return {"ok": True, "message": "Serviço desativado"}


@admin_router.get("/professionals")
def list_admin_professionals(
    include_inactive: bool = Query(default=True),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    query = db.query(Professional).options(
        selectinload(Professional.service_links),
        selectinload(Professional.hours),
    ).filter(Professional.store_id == store_id)
    if not include_inactive:
        query = query.filter(Professional.is_active.is_(True))
    return [_professional_dict(item) for item in query.order_by(Professional.name).all()]


@admin_router.post("/professionals", status_code=201)
def create_admin_professional(
    data: ProfessionalCreate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    enforce_limit(db, store_id, "professionals")
    professional = create_professional(db, store_id, data)
    professional = (
        db.query(Professional)
        .options(selectinload(Professional.service_links), selectinload(Professional.hours))
        .filter(Professional.id == professional.id)
        .one()
    )
    return _professional_dict(professional)


@admin_router.put("/professionals/{professional_id}")
def update_admin_professional(
    professional_id: int,
    data: ProfessionalUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    current = get_professional_for_store(db, store_id, professional_id)
    if not current:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    if data.is_active is True and not current.is_active:
        enforce_limit(db, store_id, "professionals")
    professional = update_professional(db, store_id, professional_id, data)
    professional = (
        db.query(Professional)
        .options(selectinload(Professional.service_links), selectinload(Professional.hours))
        .filter(Professional.id == professional.id)
        .one()
    )
    return _professional_dict(professional)


@admin_router.delete("/professionals/{professional_id}")
def deactivate_admin_professional(
    professional_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    professional = get_professional_for_store(db, store_id, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    professional.is_active = False
    db.commit()
    return {"ok": True, "message": "Profissional desativado"}


@admin_router.put("/professionals/{professional_id}/services")
def set_admin_professional_services(
    professional_id: int,
    data: ProfessionalServicesUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    replace_professional_services(db, store_id, professional_id, data)
    professional = (
        db.query(Professional)
        .options(selectinload(Professional.service_links), selectinload(Professional.hours))
        .filter(Professional.id == professional_id, Professional.store_id == store_id)
        .one()
    )
    return _professional_dict(professional)


@admin_router.put("/professionals/{professional_id}/hours")
def set_admin_professional_hours(
    professional_id: int,
    data: ProfessionalHoursUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    replace_professional_hours(db, store_id, professional_id, data)
    professional = (
        db.query(Professional)
        .options(selectinload(Professional.service_links), selectinload(Professional.hours))
        .filter(Professional.id == professional_id, Professional.store_id == store_id)
        .one()
    )
    return _professional_dict(professional)


@appointments_admin_router.get("/appointments")
def list_admin_appointments(
    status: str | None = Query(default=None),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    query = (
        db.query(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
            selectinload(Appointment.professional),
        )
        .filter(Appointment.store_id == store_id)
    )
    if status:
        query = query.filter(Appointment.status == status)
    rows = query.order_by(Appointment.starts_at.desc()).all()
    return [_appointment_dict(row, payment_for_reference(db, store_id, "APPOINTMENT", row.id)) for row in rows]


@appointments_admin_router.get("/appointments/{appointment_id}")
def get_admin_appointment(
    appointment_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    appointment = (
        db.query(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
            selectinload(Appointment.professional),
        )
        .filter(Appointment.id == appointment_id, Appointment.store_id == store_id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return _appointment_dict(appointment, payment_for_reference(db, store_id, "APPOINTMENT", appointment.id))


@appointments_admin_router.patch("/appointments/{appointment_id}/status")
def patch_admin_appointment_status(
    appointment_id: int,
    data: AppointmentStatusUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _require_capability(db, store_id, "appointments")
    appointment = (
        db.query(Appointment)
        .options(
            selectinload(Appointment.customer),
            selectinload(Appointment.service),
            selectinload(Appointment.professional),
        )
        .filter(Appointment.id == appointment_id, Appointment.store_id == store_id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    appointment = update_appointment_status(db, appointment, data.status)
    return _appointment_dict(appointment, payment_for_reference(db, store_id, "APPOINTMENT", appointment.id))
