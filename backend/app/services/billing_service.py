from sqlalchemy.orm import Session, selectinload

from ..billing.registry import provider_statuses
from ..models import BillingGatewayPrice, Plan, SubscriptionInvoice
from .subscription_service import plan_context


def _invoice_dict(row: SubscriptionInvoice) -> dict:
    return {
        "id": row.id,
        "provider": row.provider,
        "status": row.status,
        "amount": row.amount,
        "currency": row.currency,
        "payment_method": row.payment_method,
        "due_at": row.due_at,
        "paid_at": row.paid_at,
        "failed_at": row.failed_at,
        "created_at": row.created_at,
    }


def _gateway_price_dict(row: BillingGatewayPrice) -> dict:
    return {
        "id": row.id,
        "plan_id": row.plan_id,
        "plan_name": row.plan.name if row.plan else None,
        "provider": row.provider,
        "billing_cycle": row.billing_cycle,
        "currency": row.currency,
        "amount": row.amount,
        "external_plan_id": row.external_plan_id,
        "external_price_id": row.external_price_id,
        "is_active": row.is_active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def admin_billing_overview(db: Session, store_id: int) -> dict:
    invoices = (
        db.query(SubscriptionInvoice)
        .filter(SubscriptionInvoice.store_id == store_id)
        .order_by(SubscriptionInvoice.created_at.desc(), SubscriptionInvoice.id.desc())
        .limit(20)
        .all()
    )
    return {
        "subscription": plan_context(db, store_id),
        "providers": provider_statuses(),
        "recent_invoices": [_invoice_dict(row) for row in invoices],
    }


def list_gateway_prices(db: Session) -> list[dict]:
    rows = (
        db.query(BillingGatewayPrice)
        .options(selectinload(BillingGatewayPrice.plan))
        .order_by(BillingGatewayPrice.provider, BillingGatewayPrice.plan_id, BillingGatewayPrice.billing_cycle)
        .all()
    )
    return [_gateway_price_dict(row) for row in rows]


def ensure_plan(db: Session, plan_id: int) -> Plan | None:
    return db.query(Plan).filter(Plan.id == plan_id).first()


def gateway_price_dict(row: BillingGatewayPrice) -> dict:
    return _gateway_price_dict(row)
