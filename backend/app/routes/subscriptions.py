from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id, get_current_super_admin
from ..models import Plan, Store, Subscription, User
from ..schemas.subscriptions import PlanCreate, PlanUpdate, StoreSubscriptionUpdate
from ..services.subscription_service import plan_context

public_router = APIRouter(prefix="/api", tags=["plans-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["subscriptions-admin"])
super_router = APIRouter(prefix="/api/super-admin", tags=["subscriptions-super-admin"])


def _plan_dict(plan: Plan):
    return {
        "id": plan.id,
        "name": plan.name,
        "code": plan.code,
        "description": plan.description,
        "monthly_price": plan.monthly_price,
        "yearly_price": plan.yearly_price,
        "limits": plan.limits or {},
        "features": plan.features or {},
        "is_active": plan.is_active,
        "sort_order": plan.sort_order,
    }


def _subscription_dict(row: Subscription):
    return {
        "id": row.id,
        "store_id": row.store_id,
        "store_name": row.store.name if row.store else None,
        "plan": _plan_dict(row.plan) if row.plan else None,
        "status": row.status,
        "billing_cycle": row.billing_cycle,
        "starts_at": row.starts_at,
        "current_period_start": row.current_period_start,
        "current_period_end": row.current_period_end,
        "trial_ends_at": row.trial_ends_at,
        "canceled_at": row.canceled_at,
        "provider": row.provider,
        "provider_status": row.provider_status,
        "auto_renew": row.auto_renew,
        "cancel_at_period_end": row.cancel_at_period_end,
        "next_billing_at": row.next_billing_at,
        "created_at": row.created_at,
    }


@public_router.get("/plans")
def public_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.sort_order, Plan.id).all()
    return [_plan_dict(plan) for plan in plans]


@admin_router.get("/subscription")
def admin_subscription(
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    return plan_context(db, store_id)


@super_router.get("/plans")
def list_plans(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    return [_plan_dict(p) for p in db.query(Plan).order_by(Plan.sort_order, Plan.id).all()]


@super_router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanCreate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if db.query(Plan.id).filter(Plan.code == data.code).first():
        raise HTTPException(status_code=409, detail="Já existe um plano com este código")
    plan = Plan(**data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_dict(plan)


@super_router.patch("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    data: PlanUpdate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return _plan_dict(plan)


@super_router.get("/subscriptions")
def list_subscriptions(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.store))
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .all()
    )
    return [_subscription_dict(row) for row in rows]


@super_router.put("/stores/{store_id}/subscription")
def set_store_subscription(
    store_id: int,
    data: StoreSubscriptionUpdate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    plan = db.query(Plan).filter(Plan.id == data.plan_id, Plan.is_active.is_(True)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou inativo")

    now = datetime.now(timezone.utc)
    active_rows = db.query(Subscription).filter(
        Subscription.store_id == store_id,
        Subscription.status.in_(["TRIAL", "ACTIVE", "PAST_DUE"]),
    ).all()
    for row in active_rows:
        row.status = "CANCELED"
        row.canceled_at = now
        row.updated_at = now

    subscription = Subscription(
        store_id=store_id,
        plan_id=plan.id,
        status=data.status,
        billing_cycle=data.billing_cycle,
        starts_at=now,
        current_period_start=now,
        current_period_end=data.current_period_end,
        trial_ends_at=data.trial_ends_at,
        provider="MANUAL",
        created_at=now,
        updated_at=now,
    )
    if data.status == "CANCELED":
        subscription.canceled_at = now
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    subscription = (
        db.query(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.store))
        .filter(Subscription.id == subscription.id)
        .one()
    )
    return _subscription_dict(subscription)
