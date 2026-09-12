import hashlib
import json
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..billing.mercado_pago import MercadoPagoError, MercadoPagoGateway
from ..billing.registry import get_gateway, provider_statuses
from ..config import settings
from ..database import get_db
from ..dependencies import get_current_store_admin, get_current_store_id, get_current_super_admin
from ..models import BillingCoupon, BillingGatewayPrice, BillingWebhookEvent, Plan, SubscriptionInvoice, User
from ..schemas.billing import (
    AdminPlanChangeRequest,
    BillingCouponCreate,
    BillingCouponUpdate,
    BillingCouponValidateRequest,
    GatewayPriceCreate,
    GatewayPriceUpdate,
    InvoiceStatusUpdate,
    PlanChangeInvoiceCreate,
    PixCheckoutCreate,
    RenewalInvoiceCreate,
    SubscriptionCancelRequest,
)
from ..services.audit_service import write_audit
from ..services.billing_service import (
    admin_billing_overview,
    apply_invoice_status,
    amount_for_plan,
    billing_coupon_dict,
    cancel_subscription,
    create_plan_change_invoice,
    create_renewal_invoice,
    ensure_plan,
    gateway_price_dict,
    get_invoice,
    get_store_subscription,
    get_subscription,
    invoice_dict,
    list_gateway_prices,
    list_invoices,
    process_due_billing,
    sync_billing_coupon_plans,
    validate_billing_coupon,
)

public_router = APIRouter(prefix="/api/billing", tags=["subscription-billing-webhooks"])
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


@admin_router.get("/available-plans")
def admin_available_plans(
    _store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    plans = db.query(Plan).filter(Plan.is_active.is_(True), Plan.is_public.is_(True)).order_by(Plan.sort_order, Plan.id).all()
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "code": plan.code,
            "description": plan.description,
            "monthly_price": plan.monthly_price,
            "yearly_price": plan.yearly_price,
            "limits": plan.limits or {},
            "features": plan.features or {},
            "trial_days": plan.trial_days,
            "grace_days": plan.grace_days,
            "is_featured": plan.is_featured,
            "badge": plan.badge,
        }
        for plan in plans
    ]


@admin_router.post("/validate-coupon")
def admin_validate_billing_coupon(
    data: BillingCouponValidateRequest,
    _store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    plan = ensure_plan(db, data.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou inativo")
    try:
        subtotal = amount_for_plan(plan, data.billing_cycle)
        coupon, discount, total = validate_billing_coupon(
            db, data.coupon_code, plan=plan, billing_cycle=data.billing_cycle, amount=subtotal
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "valid": True,
        "coupon": billing_coupon_dict(db, coupon) if coupon else None,
        "plan_id": plan.id,
        "billing_cycle": data.billing_cycle,
        "subtotal_amount": subtotal,
        "discount_amount": discount,
        "amount": total,
    }


@admin_router.post("/change-plan", status_code=status.HTTP_201_CREATED)
def admin_request_plan_change(
    data: AdminPlanChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_store_admin),
    db: Session = Depends(get_db),
):
    store_id = current_user.store_id
    subscription = get_store_subscription(db, store_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura atual não encontrada")
    plan = ensure_plan(db, data.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou inativo")
    if subscription.plan_id == plan.id and subscription.billing_cycle == data.billing_cycle:
        raise HTTPException(
            status_code=400,
            detail="Este já é o seu plano atual neste ciclo de cobrança.",
        )
    try:
        invoice, created = create_plan_change_invoice(
            db,
            subscription,
            plan=plan,
            billing_cycle=data.billing_cycle,
            coupon_code=data.coupon_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(
        db, request, current_user,
        action="ADMIN_PLAN_CHANGE_REQUESTED" if created else "ADMIN_PLAN_CHANGE_UPDATED",
        store_id=store_id, entity_type="subscription_invoice", entity_id=invoice.id,
        metadata={"target_plan_id": plan.id, "billing_cycle": data.billing_cycle, "coupon_code": invoice.coupon_code},
    )
    db.commit()
    row = get_invoice(db, invoice.id)
    return {
        "created": created,
        "message": "Solicitação criada. O novo plano será ativado após a confirmação do pagamento.",
        "invoice": invoice_dict(row or invoice),
    }



def _mercado_pago_gateway() -> MercadoPagoGateway:
    gateway = get_gateway("MERCADO_PAGO")
    if not isinstance(gateway, MercadoPagoGateway) or not gateway.pix_ready:
        raise HTTPException(
            status_code=503,
            detail="Pix do Mercado Pago ainda não está configurado. Defina as credenciais seguras no Render.",
        )
    return gateway


def _pix_invoice_payload(invoice: SubscriptionInvoice, *, include_qr: bool = True) -> dict:
    payload = invoice_dict(invoice)
    payload.update({
        "pix_qr_code": invoice.pix_qr_code if include_qr else None,
        "pix_qr_code_base64": invoice.pix_qr_code_base64 if include_qr else None,
        "pix_ticket_url": invoice.checkout_url,
    })
    return payload


def _sync_mp_payment(db: Session, invoice: SubscriptionInvoice, payment: dict) -> SubscriptionInvoice:
    payment_id = str(payment.get("id") or "")
    expected_reference = f"saas_invoice_{invoice.id}"
    if payment.get("external_reference") != expected_reference:
        raise ValueError("Referência do pagamento não corresponde à fatura")
    if payment_id and invoice.external_payment_id and payment_id != str(invoice.external_payment_id):
        raise ValueError("Pagamento não corresponde à fatura")

    amount = Decimal(str(payment.get("transaction_amount") or "0")).quantize(Decimal("0.01"))
    expected_amount = Decimal(invoice.amount or 0).quantize(Decimal("0.01"))
    if amount != expected_amount:
        raise ValueError("Valor confirmado pelo gateway diverge da fatura")
    currency = str(payment.get("currency_id") or invoice.currency or "BRL").upper()
    if currency != str(invoice.currency or "BRL").upper():
        raise ValueError("Moeda do pagamento diverge da fatura")
    method = str(payment.get("payment_method_id") or "").lower()
    if method and method != "pix":
        raise ValueError("A fatura Pix recebeu um meio de pagamento inesperado")

    invoice.external_payment_id = payment_id or invoice.external_payment_id
    mp_status = str(payment.get("status") or "pending").lower()
    invoice.provider_status = mp_status
    invoice.provider = "MERCADO_PAGO"
    invoice.payment_method = "PIX"

    if mp_status == "approved":
        apply_invoice_status(db, invoice, new_status="PAID", payment_method="PIX")
        invoice.provider_status = mp_status
    elif mp_status in {"rejected"} and invoice.status != "PAID":
        if invoice.status != "FAILED":
            apply_invoice_status(
                db,
                invoice,
                new_status="FAILED",
                payment_method="PIX",
                failure_reason=str(payment.get("status_detail") or "Pagamento Pix rejeitado"),
            )
        invoice.provider_status = mp_status
    elif mp_status in {"cancelled", "canceled"} and invoice.status != "PAID":
        if invoice.status != "CANCELED":
            apply_invoice_status(db, invoice, new_status="CANCELED", payment_method="PIX")
        invoice.provider_status = mp_status
    elif mp_status in {"refunded", "charged_back"}:
        # Não removemos acesso automaticamente após uma reversão já paga: o Super Admin
        # recebe o estado para revisão financeira, evitando cancelamento indevido.
        invoice.provider_status = mp_status
        if invoice.status == "PAID":
            invoice.failure_reason = f"Pagamento {mp_status}; requer revisão do Super Admin."
        else:
            invoice.status = "CANCELED"
    elif invoice.status != "PAID":
        invoice.status = "PENDING"
        invoice.failure_reason = None

    db.flush()
    return invoice


@admin_router.post("/pix/checkout", status_code=status.HTTP_201_CREATED)
def admin_create_pix_checkout(
    data: PixCheckoutCreate,
    request: Request,
    current_user: User = Depends(get_current_store_admin),
    db: Session = Depends(get_db),
):
    gateway = _mercado_pago_gateway()
    store_id = current_user.store_id
    subscription = get_store_subscription(db, store_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura atual não encontrada")
    plan = ensure_plan(db, data.plan_id)
    if not plan or not plan.is_active or not plan.is_public:
        raise HTTPException(status_code=404, detail="Plano não encontrado ou indisponível")

    same_plan_cycle = subscription.plan_id == plan.id and subscription.billing_cycle == data.billing_cycle
    try:
        if same_plan_cycle:
            invoice = (
                db.query(SubscriptionInvoice)
                .filter(
                    SubscriptionInvoice.store_id == store_id,
                    SubscriptionInvoice.subscription_id == subscription.id,
                    SubscriptionInvoice.invoice_type == "RENEWAL",
                    SubscriptionInvoice.status.in_(["PENDING", "FAILED"]),
                )
                .order_by(SubscriptionInvoice.id.desc())
                .first()
            )
            if not invoice and subscription.status == "TRIAL":
                invoice, _created = create_renewal_invoice(
                    db, subscription, due_at=subscription.trial_ends_at or subscription.current_period_end
                )
            if not invoice:
                raise HTTPException(
                    status_code=400,
                    detail="Seu plano atual já está ativo. A cobrança de renovação será liberada próximo ao vencimento.",
                )
        else:
            invoice, _created = create_plan_change_invoice(
                db,
                subscription,
                plan=plan,
                billing_cycle=data.billing_cycle,
                coupon_code=data.coupon_code,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if Decimal(invoice.amount or 0) <= 0:
        raise HTTPException(status_code=400, detail="Esta cobrança não exige Pix")
    if invoice.status == "PAID":
        raise HTTPException(status_code=409, detail="Esta fatura já foi paga")

    # Reaproveita um Pix ainda pendente; retry de pagamento rejeitado recebe nova chave.
    if invoice.external_payment_id and invoice.provider_status in {"pending", "in_process"} and invoice.pix_qr_code:
        row = get_invoice(db, invoice.id) or invoice
        return {"created": False, "invoice": _pix_invoice_payload(row)}

    invoice.provider = "MERCADO_PAGO"
    invoice.payment_method = "PIX"
    if invoice.status == "FAILED":
        invoice.status = "PENDING"
        invoice.failed_at = None
        invoice.failure_reason = None
    if not invoice.provider_idempotency_key or invoice.provider_status in {"rejected", "cancelled", "canceled"}:
        invoice.provider_idempotency_key = str(uuid.uuid4())
        invoice.external_payment_id = None
        invoice.external_invoice_id = None
        invoice.pix_qr_code = None
        invoice.pix_qr_code_base64 = None
        invoice.checkout_url = None
    db.commit()

    document = data.payer_document
    document_type = "CPF" if len(document) == 11 else "CNPJ"
    notification_url = settings.mercado_pago_webhook_url
    if not notification_url and settings.public_api_base_url:
        notification_url = f"{settings.public_api_base_url}/api/billing/webhooks/mercado-pago"

    try:
        result = gateway.create_pix_payment(
            amount=Decimal(invoice.amount),
            description=f"Catálogo Digital - {plan.name}",
            payer_email=data.payer_email,
            document_type=document_type,
            document_number=document,
            external_reference=f"saas_invoice_{invoice.id}",
            idempotency_key=invoice.provider_idempotency_key,
            notification_url=notification_url,
        )
    except MercadoPagoError as exc:
        invoice = get_invoice(db, invoice.id) or invoice
        invoice.provider_status = "gateway_error"
        invoice.failure_reason = str(exc)[:500]
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    invoice = get_invoice(db, invoice.id) or invoice
    invoice.external_payment_id = result.payment_id
    invoice.external_invoice_id = result.order_id or result.payment_id
    invoice.provider_status = result.status
    invoice.pix_qr_code = result.qr_code
    invoice.pix_qr_code_base64 = result.qr_code_base64
    invoice.checkout_url = result.ticket_url
    try:
        _sync_mp_payment(db, invoice, result.raw)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Pagamento criado, mas a validação retornou erro: {exc}") from exc

    _audit(
        db,
        request,
        current_user,
        action="ADMIN_PIX_CHECKOUT_CREATED",
        store_id=store_id,
        entity_type="subscription_invoice",
        entity_id=invoice.id,
        metadata={"plan_id": plan.id, "billing_cycle": data.billing_cycle, "provider": "MERCADO_PAGO"},
    )
    db.commit()
    row = get_invoice(db, invoice.id) or invoice
    return {"created": True, "invoice": _pix_invoice_payload(row)}


@admin_router.get("/pix/invoices/{invoice_id}")
def admin_refresh_pix_invoice(
    invoice_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    gateway = _mercado_pago_gateway()
    invoice = get_invoice(db, invoice_id)
    if not invoice or invoice.store_id != store_id:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    if invoice.provider != "MERCADO_PAGO" or not invoice.external_payment_id:
        return {"invoice": _pix_invoice_payload(invoice)}
    try:
        if invoice.external_invoice_id and str(invoice.external_invoice_id).startswith("ORD"):
            payment = gateway.getorder_as_payment(str(invoice.external_invoice_id))
        else:
            payment = gateway.get_payment(str(invoice.external_payment_id))
        _sync_mp_payment(db, invoice, payment)
        db.commit()
    except MercadoPagoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    row = get_invoice(db, invoice.id) or invoice
    return {"invoice": _pix_invoice_payload(row)}


@public_router.post("/webhooks/mercado-pago")
async def mercado_pago_webhook(request: Request, db: Session = Depends(get_db)):
    gateway = get_gateway("MERCADO_PAGO")
    if not isinstance(gateway, MercadoPagoGateway) or not settings.mercado_pago_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook Mercado Pago não configurado")

    raw = await request.body()
    try:
        body = json.loads(raw.decode("utf-8")) if raw else {}
    except Exception:
        body = {}
    resource_id = (
        request.query_params.get("data.id")
        or request.query_params.get("data_id")
        or str((body.get("data") or {}).get("id") or "")
    )
    if not resource_id:
        raise HTTPException(status_code=400, detail="Notificação sem identificador")

    if not gateway.validate_webhook_signature(
        x_signature=request.headers.get("x-signature"),
        x_request_id=request.headers.get("x-request-id"),
        data_id=resource_id,
        secret=settings.mercado_pago_webhook_secret,
    ):
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida")

    external_event_id = str(body.get("id") or request.headers.get("x-request-id") or f"{body.get('type') or 'event'}:{resource_id}")
    existing = db.query(BillingWebhookEvent).filter(
        BillingWebhookEvent.provider == "MERCADO_PAGO",
        BillingWebhookEvent.external_event_id == external_event_id,
    ).first()
    if existing and existing.status in {"PROCESSED", "IGNORED"}:
        return {"ok": True, "duplicate": True}

    event = existing or BillingWebhookEvent(
        provider="MERCADO_PAGO",
        external_event_id=external_event_id,
        event_type=str(body.get("type") or body.get("action") or "payment"),
        resource_id=resource_id,
        status="RECEIVED",
        payload_hash=hashlib.sha256(raw).hexdigest(),
    )
    if existing:
        event.status = "RECEIVED"
        event.error_message = None
        event.payload_hash = hashlib.sha256(raw).hexdigest()
        event.resource_id = resource_id
    else:
        db.add(event)
    db.flush()

    event_type = str(body.get("type") or "").lower()
    if event_type not in {"order", "payment", ""}:
        event.status = "IGNORED"
        db.commit()
        return {"ok": True, "ignored": True}

    try:
        if event_type == "order" or resource_id.startswith("ORD"):
            order = gateway.get_order(resource_id)
            payment = gateway.order_as_payment(order)
            external_reference = str(order.get("external_reference") or "")
        else:
            payment = gateway.get_payment(resource_id)
            external_reference = str(payment.get("external_reference") or "")

        invoice = None
        if external_reference.startswith("saas_invoice_"):
            try:
                invoice_id = int(external_reference.rsplit("_", 1)[-1])
            except ValueError:
                invoice_id = 0
            if invoice_id:
                invoice = get_invoice(db, invoice_id)
        if not invoice and (event_type == "order" or resource_id.startswith("ORD")):
            invoice = db.query(SubscriptionInvoice).filter(
                SubscriptionInvoice.provider == "MERCADO_PAGO",
                SubscriptionInvoice.external_invoice_id == resource_id,
            ).first()
        if not invoice:
            invoice = db.query(SubscriptionInvoice).filter(
                SubscriptionInvoice.provider == "MERCADO_PAGO",
                SubscriptionInvoice.external_payment_id == resource_id,
            ).first()
        if not invoice:
            event.status = "IGNORED"
            event.error_message = "Pagamento sem fatura SaaS correspondente"
        else:
            _sync_mp_payment(db, invoice, payment)
            event.status = "PROCESSED"
    except (MercadoPagoError, ValueError) as exc:
        from datetime import datetime, timezone
        event.status = "FAILED"
        event.error_message = str(exc)[:1000]
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
        # Resposta não-2xx permite que o provedor repita uma notificação transitória.
        raise HTTPException(status_code=502, detail="Falha temporária ao processar a notificação") from exc

    from datetime import datetime, timezone
    event.processed_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@super_router.get("/providers")
def super_billing_providers(
    _super_admin: User = Depends(get_current_super_admin),
):
    return provider_statuses()


@super_router.get("/coupons")
def super_list_billing_coupons(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(BillingCoupon).order_by(BillingCoupon.created_at.desc(), BillingCoupon.id.desc()).all()
    return [billing_coupon_dict(db, row) for row in rows]


@super_router.post("/coupons", status_code=status.HTTP_201_CREATED)
def super_create_billing_coupon(
    data: BillingCouponCreate,
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if data.discount_type == "PERCENT" and data.value > 100:
        raise HTTPException(status_code=400, detail="Percentual não pode ultrapassar 100%")
    if data.starts_at and data.ends_at and data.ends_at <= data.starts_at:
        raise HTTPException(status_code=400, detail="A data final deve ser posterior à inicial")
    if db.query(BillingCoupon.id).filter(BillingCoupon.code == data.code).first():
        raise HTTPException(status_code=409, detail="Já existe um cupom de plano com este código")
    payload = data.model_dump(exclude={"plan_ids"})
    row = BillingCoupon(**payload)
    db.add(row)
    db.flush()
    try:
        sync_billing_coupon_plans(db, row, data.plan_ids)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(db, request, super_admin, action="BILLING_COUPON_CREATED", entity_type="billing_coupon", entity_id=row.id, metadata={"code": row.code})
    db.commit()
    db.refresh(row)
    return billing_coupon_dict(db, row)


@super_router.patch("/coupons/{coupon_id}")
def super_update_billing_coupon(
    coupon_id: int,
    data: BillingCouponUpdate,
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BillingCoupon).filter(BillingCoupon.id == coupon_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Cupom de plano não encontrado")
    if data.discount_type == "PERCENT" and data.value > 100:
        raise HTTPException(status_code=400, detail="Percentual não pode ultrapassar 100%")
    if data.starts_at and data.ends_at and data.ends_at <= data.starts_at:
        raise HTTPException(status_code=400, detail="A data final deve ser posterior à inicial")
    duplicate = db.query(BillingCoupon.id).filter(BillingCoupon.code == data.code, BillingCoupon.id != coupon_id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Já existe um cupom de plano com este código")
    for key, value in data.model_dump(exclude={"plan_ids"}).items():
        setattr(row, key, value)
    try:
        sync_billing_coupon_plans(db, row, data.plan_ids)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(db, request, super_admin, action="BILLING_COUPON_UPDATED", entity_type="billing_coupon", entity_id=row.id, metadata={"code": row.code})
    db.commit()
    db.refresh(row)
    return billing_coupon_dict(db, row)


@super_router.delete("/coupons/{coupon_id}")
def super_deactivate_billing_coupon(
    coupon_id: int,
    request: Request,
    super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BillingCoupon).filter(BillingCoupon.id == coupon_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Cupom de plano não encontrado")
    row.is_active = False
    _audit(db, request, super_admin, action="BILLING_COUPON_DEACTIVATED", entity_type="billing_coupon", entity_id=row.id, metadata={"code": row.code})
    db.commit()
    return {"ok": True}


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
            coupon_code=data.coupon_code,
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
