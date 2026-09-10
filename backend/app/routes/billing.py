from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..billing.registry import provider_statuses
from ..database import get_db
from ..dependencies import get_current_store_id, get_current_super_admin
from ..models import BillingGatewayPrice, User
from ..schemas.billing import (
    GatewayPriceCreate,
    GatewayPriceUpdate,
    InvoiceStatusUpdate,
    PlanChangeInvoiceCreate,
    RenewalInvoiceCreate,
    SubscriptionCancelRequest,
)
from ..services.audit_service import write_audit
from ..services.billing_service import (
    admin_billing_overview,
    apply_invoice_status,
    cancel_subscription,
    create_plan_change_invoice,
    create_renewal_invoice,
    ensure_plan,
    gateway_price_dict,
    get_invoice,
    get_subscription,
    invoice_dict,
    list_gateway_prices,
    list_invoices,
    process_due_billing,
)

admin_router = APIRouter(prefix="/api/admin/billing", tags=["subscription-billing-admin"])
super_router = APIRouter(prefix="/api/super-admin/billing", tags=["subscription-billing-super-admin"])


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()[:64]
    return request.client.host[:64] if request.client else None


def _audit(
    db: Session,
    request: Request,
    user: User,
    *,
    action: str,
    store_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | str | None = None,
    metadata: dict | None = None,
) -> None:
    write_audit(
        db,
        action=action,
        store_id=store_id,
        user_id=user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=_request_ip(request),
        user_agent=request.headers.get("user-agent"),
        metadata=metadata,
    )


@admin_router.get("/providers")
def admin_billing_providers(
    _store_id: int = Depends(get_current_store_id),
):
    return provider_statuses()


@admin_router.get("/overview")
def billing_overview(
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    return admin_billing_overview(db, store_id)


@super_router.get("/providers")
def super_billing_providers(
    _super_admin: User = Depends(get_current_super_admin),
):
    return provider_statuses()


@super_router.get("/gateway-prices")
def super_list_gateway_prices(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    return list_gateway_prices(db)


@super_router.post("/gateway-prices", status_code=status.HTTP_201_CREATED)
def super_create_gateway_price(
    data: GatewayPriceCreate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    plan = ensure_plan(db, data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    row = BillingGatewayPrice(**data.model_dump())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Já existe um preço para este plano, gateway, ciclo e moeda",
        )
    row = (
        db.query(BillingGatewayPrice)
        .options(selectinload(BillingGatewayPrice.plan))
        .filter(BillingGatewayPrice.id == row.id)
        .one()
    )
    return gateway_price_dict(row)


@super_router.patch("/gateway-prices/{gateway_price_id}")
def super_update_gateway_price(
    gateway_price_id: int,
    data: GatewayPriceUpdate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BillingGatewayPrice).filter(BillingGatewayPrice.id == gateway_price_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Preço de gateway não encontrado")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    row = (
        db.query(BillingGatewayPrice)
        .options(selectinload(BillingGatewayPrice.plan))
        .filter(BillingGatewayPrice.id == gateway_price_id)
        .one()
    )
    return gateway_price_dict(row)


@super_router.get("/invoices")
def super_list_invoices(
    store_id: int | None = Query(default=None, gt=0),
    invoice_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if invoice_status:
        invoice_status = invoice_status.strip().upper()
        if invoice_status not in {"PENDING", "PAID", "FAILED", "CANCELED"}:
            raise HTTPException(status_code=422, detail="Status de fatura inválido")
    return list_invoices(db, store_id=store_id, invoice_status=invoice_status, limit=limit)


@super_router.post("/subscriptions/{subscription_id}/renewal-invoice", status_code=status.HTTP_201_CREATED)
def super_create_renewal_invoice(
    subscription_id: int,
    data: RenewalInvoiceCreate,
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    subscription = get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    try:
        invoice, created = create_renewal_invoice(
            db,
            subscription,
            due_at=data.due_at,
            payment_method=data.payment_method,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _audit(
        db,
        request,
        super_admin,
        action="BILLING_RENEWAL_INVOICE_CREATED" if created else "BILLING_RENEWAL_INVOICE_REUSED",
        store_id=subscription.store_id,
        entity_type="subscription_invoice",
        entity_id=invoice.id,
        metadata={"subscription_id": subscription.id, "created": created},
    )
    db.commit()
    row = get_invoice(db, invoice.id)
    return {"created": created, "invoice": invoice_dict(row or invoice)}


@super_router.post("/subscriptions/{subscription_id}/change-plan", status_code=status.HTTP_201_CREATED)
def super_request_plan_change(
    subscription_id: int,
    data: PlanChangeInvoiceCreate,
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    subscription = get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    plan = ensure_plan(db, data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    try:
        invoice, created = create_plan_change_invoice(
            db,
            subscription,
            plan=plan,
            billing_cycle=data.billing_cycle,
            due_at=data.due_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _audit(
        db,
        request,
        super_admin,
        action="BILLING_PLAN_CHANGE_REQUESTED" if created else "BILLING_PLAN_CHANGE_REUSED",
        store_id=subscription.store_id,
        entity_type="subscription_invoice",
        entity_id=invoice.id,
        metadata={
            "subscription_id": subscription.id,
            "target_plan_id": plan.id,
            "billing_cycle": data.billing_cycle,
            "created": created,
        },
    )
    db.commit()
    row = get_invoice(db, invoice.id)
    return {"created": created, "invoice": invoice_dict(row or invoice)}


@super_router.patch("/invoices/{invoice_id}/status")
def super_update_invoice_status(
    invoice_id: int,
    data: InvoiceStatusUpdate,
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    invoice = get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    old_status = invoice.status
    try:
        invoice = apply_invoice_status(
            db,
            invoice,
            new_status=data.status,
            payment_method=data.payment_method,
            failure_reason=data.failure_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _audit(
        db,
        request,
        super_admin,
        action="BILLING_INVOICE_STATUS_CHANGED",
        store_id=invoice.store_id,
        entity_type="subscription_invoice",
        entity_id=invoice.id,
        metadata={"from": old_status, "to": invoice.status, "invoice_type": invoice.invoice_type},
    )
    db.commit()
    row = get_invoice(db, invoice.id)
    return invoice_dict(row or invoice)


@super_router.post("/subscriptions/{subscription_id}/cancel")
def super_cancel_subscription(
    subscription_id: int,
    data: SubscriptionCancelRequest,
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    subscription = get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

    cancel_subscription(subscription, at_period_end=data.at_period_end)
    _audit(
        db,
        request,
        super_admin,
        action="BILLING_SUBSCRIPTION_CANCEL_REQUESTED",
        store_id=subscription.store_id,
        entity_type="subscription",
        entity_id=subscription.id,
        metadata={"at_period_end": data.at_period_end, "result_status": subscription.status},
    )
    db.commit()
    subscription = get_subscription(db, subscription.id)
    return {
        "id": subscription.id,
        "store_id": subscription.store_id,
        "status": subscription.status,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "current_period_end": subscription.current_period_end,
        "canceled_at": subscription.canceled_at,
        "next_billing_at": subscription.next_billing_at,
    }


@super_router.post("/process-due")
def super_process_due_billing(
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    stats = process_due_billing(db)
    _audit(
        db,
        request,
        super_admin,
        action="BILLING_DUE_PROCESS_EXECUTED",
        entity_type="billing_engine",
        metadata=stats,
    )
    db.commit()
    return stats
