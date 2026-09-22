from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.catalog import Category
from ..models.services import Professional, ProfessionalHours, ProfessionalService, Service
from ..schemas.services import (
    ProfessionalCreate,
    ProfessionalHoursUpdate,
    ProfessionalServicesUpdate,
    ProfessionalUpdate,
    ServiceCreate,
    ServiceUpdate,
)
from ..utils.text import slugify


def _commit_or_conflict(db: Session, detail: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail)


def _category_for_store(db: Session, store_id: int, category_id: int | None):
    if category_id is None:
        return None
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.store_id == store_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=400, detail="A categoria não pertence à sua loja")
    return category


def get_service_for_store(db: Session, store_id: int, service_id: int) -> Service | None:
    return (
        db.query(Service)
        .filter(Service.id == service_id, Service.store_id == store_id)
        .first()
    )


def get_professional_for_store(db: Session, store_id: int, professional_id: int) -> Professional | None:
    return (
        db.query(Professional)
        .filter(Professional.id == professional_id, Professional.store_id == store_id)
        .first()
    )


def create_service(db: Session, store_id: int, data: ServiceCreate) -> Service:
    _category_for_store(db, store_id, data.category_id)
    service = Service(
        store_id=store_id,
        category_id=data.category_id,
        name=data.name.strip(),
        slug=slugify(data.slug or data.name),
        description=data.description,
        price=data.price,
        duration_minutes=data.duration_minutes,
        image_url=data.image_url,
        is_active=True,
    )
    db.add(service)
    _commit_or_conflict(db, "Já existe um serviço com esse slug nesta loja")
    db.refresh(service)
    return service


def update_service(db: Session, store_id: int, service_id: int, data: ServiceUpdate) -> Service:
    service = get_service_for_store(db, store_id, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    values = data.model_dump(exclude_unset=True)
    if "category_id" in values:
        _category_for_store(db, store_id, values["category_id"])
    if values.get("name") is not None:
        values["name"] = values["name"].strip()
    if values.get("slug") is not None:
        values["slug"] = slugify(values["slug"])
    for key, value in values.items():
        setattr(service, key, value)
    _commit_or_conflict(db, "Já existe um serviço com esse slug nesta loja")
    db.refresh(service)
    return service


def create_professional(db: Session, store_id: int, data: ProfessionalCreate) -> Professional:
    professional = Professional(
        store_id=store_id,
        name=data.name.strip(),
        description=data.description,
        phone=data.phone.strip() if data.phone else None,
        email=str(data.email).lower() if data.email else None,
        image_url=data.image_url,
        is_active=True,
    )
    db.add(professional)
    db.commit()
    db.refresh(professional)
    return professional


def update_professional(
    db: Session, store_id: int, professional_id: int, data: ProfessionalUpdate
) -> Professional:
    professional = get_professional_for_store(db, store_id, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    values = data.model_dump(exclude_unset=True)
    if values.get("name") is not None:
        values["name"] = values["name"].strip()
    if values.get("phone") is not None:
        values["phone"] = values["phone"].strip() or None
    if values.get("email") is not None:
        values["email"] = str(values["email"]).lower()
    for key, value in values.items():
        setattr(professional, key, value)
    db.commit()
    db.refresh(professional)
    return professional


def replace_professional_services(
    db: Session,
    store_id: int,
    professional_id: int,
    data: ProfessionalServicesUpdate,
) -> Professional:
    professional = get_professional_for_store(db, store_id, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    services = []
    if data.service_ids:
        services = (
            db.query(Service)
            .filter(
                Service.store_id == store_id,
                Service.id.in_(data.service_ids),
                Service.is_active.is_(True),
            )
            .all()
        )
        found = {service.id for service in services}
        missing = sorted(set(data.service_ids) - found)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Serviços inválidos para esta loja: {missing}",
            )

    db.query(ProfessionalService).filter(
        ProfessionalService.store_id == store_id,
        ProfessionalService.professional_id == professional_id,
    ).delete(synchronize_session=False)
    for service in services:
        db.add(
            ProfessionalService(
                store_id=store_id,
                professional_id=professional.id,
                service_id=service.id,
            )
        )
    db.commit()
    db.refresh(professional)
    return professional


def replace_professional_hours(
    db: Session,
    store_id: int,
    professional_id: int,
    data: ProfessionalHoursUpdate,
) -> Professional:
    professional = get_professional_for_store(db, store_id, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    db.query(ProfessionalHours).filter(
        ProfessionalHours.store_id == store_id,
        ProfessionalHours.professional_id == professional_id,
    ).delete(synchronize_session=False)

    for item in data.hours:
        db.add(
            ProfessionalHours(
                store_id=store_id,
                professional_id=professional_id,
                day_of_week=item.day_of_week,
                start_time=item.start_time,
                end_time=item.end_time,
                is_active=item.is_active,
            )
        )
    db.commit()
    db.refresh(professional)
    return professional
