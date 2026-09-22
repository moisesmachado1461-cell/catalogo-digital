from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..models.catalog import Product
from ..models.services import Professional, Service
from ..config import settings
from ..models.subscriptions import Plan, Subscription


ACTIVE_STATUSES = {"TRIAL", "ACTIVE", "PAST_DUE"}


def _aware(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_effective_subscription(db: Session, store_id: int) -> Subscription | None:
    rows = (
        db.query(Subscription)
        .options(selectinload(Subscription.plan))
        .filter(Subscription.store_id == store_id)
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .all()
    )
    now = datetime.now(timezone.utc)
    for row in rows:
        if row.status not in ACTIVE_STATUSES:
            continue
        if row.status == "TRIAL" and row.trial_ends_at and _aware(row.trial_ends_at) < now:
            continue
        if row.current_period_end and _aware(row.current_period_end) < now:
            if row.status != "PAST_DUE":
                continue
            grace_days = row.grace_days_snapshot
            if grace_days is None and row.plan is not None:
                grace_days = getattr(row.plan, "grace_days", None)
            if grace_days is None:
                grace_days = settings.billing_grace_days
            grace_end = _aware(row.current_period_end) + timedelta(days=int(grace_days))
            if grace_end < now:
                continue
        if row.plan:
            return row
    return None


def get_fallback_free_plan(db: Session) -> Plan | None:
    return db.query(Plan).filter(Plan.code == "GRATUITO", Plan.is_active.is_(True)).first()


def get_effective_plan(db: Session, store_id: int) -> tuple[Plan | None, Subscription | None]:
    subscription = get_effective_subscription(db, store_id)
    if subscription:
        return subscription.plan, subscription
    return get_fallback_free_plan(db), None


def usage_for_store(db: Session, store_id: int) -> dict:
    return {
        "products": db.query(func.count(Product.id)).filter(Product.store_id == store_id, Product.is_active.is_(True)).scalar() or 0,
        "services": db.query(func.count(Service.id)).filter(Service.store_id == store_id, Service.is_active.is_(True)).scalar() or 0,
        "professionals": db.query(func.count(Professional.id)).filter(Professional.store_id == store_id, Professional.is_active.is_(True)).scalar() or 0,
    }


def _subscription_terms(plan: Plan, subscription: Subscription | None) -> tuple[dict, dict, object, object, str, int, int]:
    limits = (subscription.limits_snapshot if subscription and subscription.limits_snapshot is not None else plan.limits) or {}
    features = (subscription.features_snapshot if subscription and subscription.features_snapshot is not None else plan.features) or {}
    monthly = subscription.monthly_price_snapshot if subscription and subscription.monthly_price_snapshot is not None else plan.monthly_price
    yearly = subscription.yearly_price_snapshot if subscription and subscription.yearly_price_snapshot is not None else plan.yearly_price
    name = subscription.plan_name_snapshot if subscription and subscription.plan_name_snapshot else plan.name
    trial_days = subscription.trial_days_snapshot if subscription and subscription.trial_days_snapshot is not None else getattr(plan, "trial_days", 0)
    grace_days = subscription.grace_days_snapshot if subscription and subscription.grace_days_snapshot is not None else getattr(plan, "grace_days", settings.billing_grace_days)
    return limits, features, monthly, yearly, name, int(trial_days or 0), int(grace_days or 0)


def snapshot_subscription_terms(subscription: Subscription, plan: Plan, *, now: datetime | None = None) -> Subscription:
    subscription.plan_name_snapshot = plan.name
    subscription.monthly_price_snapshot = plan.monthly_price
    subscription.yearly_price_snapshot = plan.yearly_price
    subscription.limits_snapshot = dict(plan.limits or {})
    subscription.features_snapshot = dict(plan.features or {})
    subscription.trial_days_snapshot = int(getattr(plan, "trial_days", 0) or 0)
    subscription.grace_days_snapshot = int(getattr(plan, "grace_days", settings.billing_grace_days) or 0)
    subscription.commercial_terms_at = now or datetime.now(timezone.utc)
    return subscription


def plan_context(db: Session, store_id: int) -> dict:
    plan, subscription = get_effective_plan(db, store_id)
    usage = usage_for_store(db, store_id)
    if not plan:
        return {"plan": None, "subscription": None, "usage": usage, "limits": {}, "features": {}}
    limits, features, monthly, yearly, plan_name, trial_days, grace_days = _subscription_terms(plan, subscription)
    return {
        "plan": {
            "id": plan.id,
            "name": plan_name,
            "code": plan.code,
            "description": plan.description,
            "monthly_price": monthly,
            "yearly_price": yearly,
            "trial_days": trial_days,
            "grace_days": grace_days,
            "badge": getattr(plan, "badge", None),
            "is_featured": bool(getattr(plan, "is_featured", False)),
        },
        "subscription": (
            {
                "id": subscription.id,
                "status": subscription.status,
                "billing_cycle": subscription.billing_cycle,
                "starts_at": subscription.starts_at,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_ends_at": subscription.trial_ends_at,
                "provider": subscription.provider,
                "provider_status": subscription.provider_status,
                "auto_renew": subscription.auto_renew,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "next_billing_at": subscription.next_billing_at,
                "commercial_terms_at": subscription.commercial_terms_at,
            }
            if subscription
            else None
        ),
        "usage": usage,
        "limits": limits,
        "features": features,
    }


def enforce_limit(db: Session, store_id: int, resource: str, current_count: int | None = None):
    plan, subscription = get_effective_plan(db, store_id)
    if not plan:
        return
    limits, _features, _monthly, _yearly, _name, _trial, _grace = _subscription_terms(plan, subscription)
    limit = limits.get(resource, -1)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = -1
    if limit < 0:
        return
    if current_count is None:
        current_count = usage_for_store(db, store_id).get(resource, 0)
    if current_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Limite do plano atingido para {resource}: {current_count}/{limit}. Altere o plano para continuar.",
        )



def feature_enabled(db: Session, store_id: int, feature: str) -> bool:
    plan, subscription = get_effective_plan(db, store_id)
    if not plan:
        return True
    _limits, features, _monthly, _yearly, _name, _trial, _grace = _subscription_terms(plan, subscription)
    return bool(features.get(feature, False))

def require_feature(db: Session, store_id: int, feature: str):
    plan, _subscription = get_effective_plan(db, store_id)
    if not plan:
        return
    if not feature_enabled(db, store_id, feature):
        raise HTTPException(
            status_code=403,
            detail=f"O recurso '{feature}' não está disponível no plano {plan.name}.",
        )
