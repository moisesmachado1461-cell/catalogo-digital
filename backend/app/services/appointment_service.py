from datetime import date, datetime, timedelta, timezone
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.sales import Customer
from ..models.services import Appointment, Professional, ProfessionalBlock, ProfessionalHours, ProfessionalService, Service
from ..models.store import Store
from ..schemas.services import AppointmentCreate
from .payment_service import cancel_reference_payment, create_payment

ACTIVE_CONFLICT_STATUSES = {"PENDENTE", "CONFIRMADO"}
ALLOWED_TRANSITIONS = {
    "PENDENTE": {"CONFIRMADO", "CANCELADO"},
    "CONFIRMADO": {"CONCLUIDO", "CANCELADO", "NAO_COMPARECEU"},
    "CONCLUIDO": set(),
    "CANCELADO": set(),
    "NAO_COMPARECEU": set(),
}


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise HTTPException(status_code=400, detail="Data/hora deve incluir fuso horário")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _new_public_token(db: Session) -> str:
    for _ in range(5):
        token = secrets.token_urlsafe(18)
        exists = db.query(Appointment.id).filter(Appointment.public_token == token).first()
        if not exists:
            return token
    raise HTTPException(status_code=500, detail="Não foi possível gerar o protocolo do agendamento")


def _find_or_create_customer(db: Session, store_id: int, data) -> Customer:
    customer = None
    if data.email:
        customer = (
            db.query(Customer)
            .filter(Customer.store_id == store_id, Customer.email == str(data.email).lower())
            .first()
        )
    if not customer and data.phone:
        customer = (
            db.query(Customer)
            .filter(Customer.store_id == store_id, Customer.phone == data.phone.strip())
            .first()
        )
    if not customer:
        customer = Customer(
            store_id=store_id,
            name=data.name.strip(),
            email=str(data.email).lower() if data.email else None,
            phone=data.phone.strip() if data.phone else None,
            is_active=True,
        )
        db.add(customer)
        db.flush()
    else:
        customer.name = data.name.strip()
        if data.email:
            customer.email = str(data.email).lower()
        if data.phone:
            customer.phone = data.phone.strip()
    return customer


def _validate_pair(db: Session, store_id: int, service_id: int, professional_id: int):
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.store_id == store_id, Service.is_active.is_(True))
        .first()
    )
    if not service:
        raise HTTPException(status_code=400, detail="Serviço inválido para esta loja")

    professional = (
        db.query(Professional)
        .filter(
            Professional.id == professional_id,
            Professional.store_id == store_id,
            Professional.is_active.is_(True),
        )
        .first()
    )
    if not professional:
        raise HTTPException(status_code=400, detail="Profissional inválido para esta loja")

    link = (
        db.query(ProfessionalService)
        .filter(
            ProfessionalService.store_id == store_id,
            ProfessionalService.professional_id == professional_id,
            ProfessionalService.service_id == service_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=400, detail="Este profissional não realiza o serviço selecionado")
    return service, professional


def _validate_work_hours(
    db: Session,
    store_id: int,
    professional_id: int,
    local_start: datetime,
    local_end: datetime,
):
    hours = (
        db.query(ProfessionalHours)
        .filter(
            ProfessionalHours.store_id == store_id,
            ProfessionalHours.professional_id == professional_id,
            ProfessionalHours.day_of_week == local_start.weekday(),
            ProfessionalHours.is_active.is_(True),
        )
        .first()
    )
    if not hours:
        raise HTTPException(status_code=409, detail="Profissional não trabalha nesse dia")
    if local_start.time().replace(tzinfo=None) < hours.start_time or local_end.time().replace(tzinfo=None) > hours.end_time:
        raise HTTPException(status_code=409, detail="Horário fora da jornada do profissional")
    if local_start.date() != local_end.date():
        raise HTTPException(status_code=409, detail="O serviço não pode ultrapassar o fim do dia nesta fase")


def _has_conflict(
    db: Session,
    store_id: int,
    professional_id: int,
    start_utc_naive: datetime,
    end_utc_naive: datetime,
) -> bool:
    return (
        db.query(Appointment)
        .filter(
            Appointment.store_id == store_id,
            Appointment.professional_id == professional_id,
            Appointment.status.in_(ACTIVE_CONFLICT_STATUSES),
            Appointment.starts_at < end_utc_naive,
            Appointment.ends_at > start_utc_naive,
        )
        .first()
        is not None
    )


def _has_block(
    db: Session,
    store_id: int,
    professional_id: int,
    start_utc_naive: datetime,
    end_utc_naive: datetime,
) -> bool:
    return (
        db.query(ProfessionalBlock)
        .filter(
            ProfessionalBlock.store_id == store_id,
            ProfessionalBlock.professional_id == professional_id,
            ProfessionalBlock.starts_at < end_utc_naive,
            ProfessionalBlock.ends_at > start_utc_naive,
        )
        .first()
        is not None
    )


def create_appointment(db: Session, store: Store, data: AppointmentCreate) -> Appointment:
    if not store.is_active:
        raise HTTPException(status_code=404, detail="Loja indisponível")
    if not store.capabilities.get("appointments", False):
        raise HTTPException(status_code=403, detail="Agendamentos não estão habilitados para esta loja")

    service, _professional = _validate_pair(db, store.id, data.service_id, data.professional_id)
    local_start = data.starts_at
    local_end = local_start + timedelta(minutes=service.duration_minutes)
    start_utc_naive = _to_utc_naive(local_start)
    end_utc_naive = _to_utc_naive(local_end)

    now_utc = datetime.now(timezone.utc)
    if _as_utc(data.starts_at) <= now_utc:
        raise HTTPException(status_code=409, detail="Não é possível agendar um horário no passado")
    if _as_utc(data.starts_at) > now_utc + timedelta(days=180):
        raise HTTPException(status_code=409, detail="Agendamentos podem ser feitos com até 180 dias de antecedência")

    _validate_work_hours(db, store.id, data.professional_id, local_start, local_end)
    if _has_block(db, store.id, data.professional_id, start_utc_naive, end_utc_naive):
        raise HTTPException(status_code=409, detail="Este horário está bloqueado pelo estabelecimento")
    if _has_conflict(db, store.id, data.professional_id, start_utc_naive, end_utc_naive):
        raise HTTPException(status_code=409, detail="Este horário não está mais disponível")

    customer = _find_or_create_customer(db, store.id, data.customer)
    appointment = Appointment(
        public_token=_new_public_token(db),
        store_id=store.id,
        customer_id=customer.id,
        service_id=service.id,
        professional_id=data.professional_id,
        starts_at=start_utc_naive,
        ends_at=end_utc_naive,
        status="PENDENTE",
        notes=data.notes,
    )
    db.add(appointment)
    db.flush()
    create_payment(
        db,
        store,
        reference_type="APPOINTMENT",
        reference_id=appointment.id,
        amount=service.price,
        method=data.payment_method,
    )
    db.commit()
    db.refresh(appointment)
    return appointment


def list_available_slots(
    db: Session,
    store: Store,
    service_id: int,
    professional_id: int,
    target_date: date,
    utc_offset_minutes: int,
    slot_interval_minutes: int,
) -> list[dict]:
    if not store.capabilities.get("appointments", False):
        raise HTTPException(status_code=403, detail="Agendamentos não estão habilitados para esta loja")
    service, _professional = _validate_pair(db, store.id, service_id, professional_id)

    fixed_tz = timezone(timedelta(minutes=utc_offset_minutes))
    local_today = datetime.now(fixed_tz).date()
    if target_date < local_today:
        return []
    if target_date > local_today + timedelta(days=180):
        raise HTTPException(status_code=409, detail="Consulte horários com até 180 dias de antecedência")

    hours = (
        db.query(ProfessionalHours)
        .filter(
            ProfessionalHours.store_id == store.id,
            ProfessionalHours.professional_id == professional_id,
            ProfessionalHours.day_of_week == target_date.weekday(),
            ProfessionalHours.is_active.is_(True),
        )
        .first()
    )
    if not hours:
        return []

    current = datetime.combine(target_date, hours.start_time, tzinfo=fixed_tz)
    closing = datetime.combine(target_date, hours.end_time, tzinfo=fixed_tz)
    now_utc = datetime.now(timezone.utc)
    slots = []
    while current + timedelta(minutes=service.duration_minutes) <= closing:
        local_end = current + timedelta(minutes=service.duration_minutes)
        start_utc_naive = _to_utc_naive(current)
        end_utc_naive = _to_utc_naive(local_end)
        is_free = (
            current.astimezone(timezone.utc) > now_utc
            and not _has_block(db, store.id, professional_id, start_utc_naive, end_utc_naive)
            and not _has_conflict(db, store.id, professional_id, start_utc_naive, end_utc_naive)
        )
        if is_free:
            slots.append({"starts_at": current.isoformat(), "ends_at": local_end.isoformat()})
        current += timedelta(minutes=slot_interval_minutes)
    return slots


def update_appointment_status(db: Session, appointment: Appointment, new_status: str) -> Appointment:
    if new_status == appointment.status:
        return appointment
    if new_status not in ALLOWED_TRANSITIONS.get(appointment.status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Transição de {appointment.status} para {new_status} não permitida",
        )
    appointment.status = new_status
    if new_status == "CANCELADO":
        cancel_reference_payment(db, appointment.store_id, "APPOINTMENT", appointment.id)
    db.commit()
    db.refresh(appointment)
    return appointment
