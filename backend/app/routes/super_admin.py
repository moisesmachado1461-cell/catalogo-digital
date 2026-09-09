from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_super_admin
from ..models import (
    Appointment,
    BusinessCategory,
    Customer,
    Order,
    Product,
    QuoteRequest,
    Store,
    User,
    Plan,
    Subscription,
)
from ..schemas.super_admin import StoreStatusUpdate, SuperAdminStoreCreate
from ..security import hash_password
from ..utils.text import slugify
from ..services.subscription_service import plan_context

router = APIRouter(prefix="/api/super-admin", tags=["super-admin"])


def _unique_slug(db: Session, raw: str) -> str:
    base = slugify(raw) or "loja"
    candidate = base
    number = 2
    while db.query(Store.id).filter(Store.slug == candidate).first():
        candidate = f"{base}-{number}"
        number += 1
    return candidate


def _store_summary(db: Session, store: Store) -> dict:
    admin = (
        db.query(User)
        .filter(
            User.store_id == store.id,
            User.role == "ADMINISTRADOR_DA_LOJA",
            User.is_active.is_(True),
        )
        .order_by(User.id)
        .first()
    )
    return {
        "id": store.id,
        "name": store.name,
        "slug": store.slug,
        "is_active": store.is_active,
        "business_model": {
            "id": store.business_model.id,
            "name": store.business_model.name,
            "code": store.business_model.code,
        } if store.business_model else None,
        "business_category": {
            "id": store.business_category.id,
            "name": store.business_category.name,
            "slug": store.business_category.slug,
        } if store.business_category else None,
        "capabilities": store.capabilities,
        "subscription": plan_context(db, store.id),
        "admin": {
            "id": admin.id,
            "name": admin.name,
            "email": admin.email,
        } if admin else None,
        "metrics": {
            "products": db.query(func.count(Product.id)).filter(Product.store_id == store.id).scalar() or 0,
            "customers": db.query(func.count(Customer.id)).filter(Customer.store_id == store.id).scalar() or 0,
            "orders": db.query(func.count(Order.id)).filter(Order.store_id == store.id).scalar() or 0,
            "appointments": db.query(func.count(Appointment.id)).filter(Appointment.store_id == store.id).scalar() or 0,
            "quotes": db.query(func.count(QuoteRequest.id)).filter(QuoteRequest.store_id == store.id).scalar() or 0,
        },
        "created_at": store.created_at,
    }


@router.get("/dashboard")
def dashboard(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total), 0))
        .filter(Order.status != "CANCELADO")
        .scalar()
    )
    return {
        "stores": db.query(func.count(Store.id)).scalar() or 0,
        "active_stores": db.query(func.count(Store.id)).filter(Store.is_active.is_(True)).scalar() or 0,
        "active_subscriptions": db.query(func.count(Subscription.id)).filter(Subscription.status.in_(["TRIAL", "ACTIVE", "PAST_DUE"])).scalar() or 0,
        "store_admins": db.query(func.count(User.id)).filter(User.role == "ADMINISTRADOR_DA_LOJA").scalar() or 0,
        "customers": db.query(func.count(Customer.id)).scalar() or 0,
        "products": db.query(func.count(Product.id)).scalar() or 0,
        "orders": db.query(func.count(Order.id)).scalar() or 0,
        "appointments": db.query(func.count(Appointment.id)).scalar() or 0,
        "quotes": db.query(func.count(QuoteRequest.id)).scalar() or 0,
        "gross_order_value": str(Decimal(total_revenue or 0).quantize(Decimal("0.01"))),
    }


@router.get("/stores")
def list_stores(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    stores = (
        db.query(Store)
        .options(selectinload(Store.business_model), selectinload(Store.business_category))
        .order_by(Store.created_at.desc(), Store.id.desc())
        .all()
    )
    return [_store_summary(db, store) for store in stores]


@router.get("/stores/{store_id}")
def get_store(
    store_id: int,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    store = (
        db.query(Store)
        .options(selectinload(Store.business_model), selectinload(Store.business_category))
        .filter(Store.id == store_id)
        .first()
    )
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    return _store_summary(db, store)


@router.post("/stores", status_code=status.HTTP_201_CREATED)
def create_store(
    data: SuperAdminStoreCreate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    email = str(data.admin_email).lower().strip()
    if db.query(User.id).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Já existe um usuário com este e-mail")

    category = (
        db.query(BusinessCategory)
        .options(selectinload(BusinessCategory.business_model))
        .filter(BusinessCategory.id == data.business_category_id, BusinessCategory.active.is_(True))
        .first()
    )
    if not category or not category.business_model or not category.business_model.active:
        raise HTTPException(status_code=400, detail="Categoria de negócio inválida ou inativa")

    requested_slug = slugify(data.slug) if data.slug else slugify(data.name)
    store_slug = _unique_slug(db, requested_slug)
    capabilities = {
        **(category.business_model.default_capabilities or {}),
        **(category.default_capabilities or {}),
    }

    try:
        store = Store(
            name=data.name.strip(),
            slug=store_slug,
            business_category_id=category.id,
            business_model_id=category.business_model.id,
            capabilities=capabilities,
            description=data.description,
            primary_color=data.primary_color,
            secondary_color=data.secondary_color,
            whatsapp=data.whatsapp,
            phone=data.phone,
            email=str(data.email) if data.email else None,
            address=data.address,
            city=data.city,
            state=data.state,
            zip_code=data.zip_code,
            is_active=True,
        )
        db.add(store)
        db.flush()

        user = User(
            name=data.admin_name.strip(),
            email=email,
            password_hash=hash_password(data.admin_password),
            role="ADMINISTRADOR_DA_LOJA",
            store_id=store.id,
            is_active=True,
            email_verified=True,
        )
        db.add(user)

        plan = None
        if data.plan_id is not None:
            plan = db.query(Plan).filter(Plan.id == data.plan_id, Plan.is_active.is_(True)).first()
            if not plan:
                raise HTTPException(status_code=400, detail="Plano informado é inválido ou está inativo")
        else:
            plan = db.query(Plan).filter(Plan.code == "GRATUITO", Plan.is_active.is_(True)).first()

        if plan:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            db.add(Subscription(
                store_id=store.id,
                plan_id=plan.id,
                status="ACTIVE",
                billing_cycle="MONTHLY",
                starts_at=now,
                current_period_start=now,
                provider="MANUAL",
                created_at=now,
                updated_at=now,
            ))
        db.commit()
    except Exception:
        db.rollback()
        raise

    store = (
        db.query(Store)
        .options(selectinload(Store.business_model), selectinload(Store.business_category))
        .filter(Store.id == store.id)
        .one()
    )
    return _store_summary(db, store)


@router.patch("/stores/{store_id}/status")
def update_store_status(
    store_id: int,
    data: StoreStatusUpdate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    store.is_active = data.is_active
    db.commit()
    return {"id": store.id, "is_active": store.is_active}


@router.get("/users")
def list_store_admins(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .filter(User.role == "ADMINISTRADOR_DA_LOJA")
        .order_by(User.created_at.desc(), User.id.desc())
        .all()
    )
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "store_id": user.store_id,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": user.created_at,
        }
        for user in users
    ]
