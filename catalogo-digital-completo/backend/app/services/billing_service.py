import calendar
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session, selectinload

from ..billing.registry import provider_statuses
from ..config import settings
from ..models import BillingCoupon, BillingCouponPlan, BillingCouponUsage, BillingGatewayPrice, Plan, Store, Subscription, SubscriptionInvoice
from .subscription_service import plan_context, snapshot_subscription_terms


ACTIVE_OR_COLLECTIBLE = {"TRIAL", "ACTIVE", "PAST_DUE"}
OPEN_INVOICE_STATUSES = {"PENDING", "FAILED"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def add_billing_cycle(start: datetime, billing_cycle: str) -> datetime:
    """Soma um ciclo preservando o dia quando possível, sem dependência externa."""
    start = aware(start) or utcnow()
    cycle = billing_cycle.strip().upper()
    if cycle == "YEARLY":
        year = start.year + 1
        day = min(start.day, calendar.monthrange(year, start.month)[1])
        return start.replace(year=year, day=day)
    if cycle != "MONTHLY":
        raise ValueError("Ciclo de cobrança inválido")

    month_index = start.month
    year = start.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)


def amount_for_plan(plan: Plan, billing_cycle: str) -> Decimal:
    cycle = billing_cycle.strip().upper()
    if cycle == "MONTHLY":
        return Decimal(plan.monthly_price or 0).quantize(Decimal("0.01"))
    if cycle == "YEARLY":
        if plan.yearly_price is None:
            raise ValueError("Este plano ainda não possui preço anual configurado")
        return Decimal(plan.yearly_price).quantize(Decimal("0.01"))
    raise ValueError("Ciclo de cobrança inválido")


def amount_for_subscription(subscription: Subscription, billing_cycle: str | None = None) -> Decimal:
    cycle = (billing_cycle or subscription.billing_cycle).strip().upper()
    if cycle == "MONTHLY" and subscription.monthly_price_snapshot is not None:
        return Decimal(subscription.monthly_price_snapshot).quantize(Decimal("0.01"))
    if cycle == "YEARLY" and subscription.yearly_price_snapshot is not None:
        return Decimal(subscription.yearly_price_snapshot).quantize(Decimal("0.01"))
    if not subscription.plan:
        raise ValueError("Assinatura sem plano associado")
    return amount_for_plan(subscription.plan, cycle)


def billing_coupon_dict(db: Session, row: BillingCoupon) -> dict:
    plan_ids = [
        item.plan_id
        for item in db.query(BillingCouponPlan).filter(BillingCouponPlan.coupon_id == row.id).order_by(BillingCouponPlan.plan_id).all()
    ]
    return {
        "id": row.id,
        "code": row.code,
        "description": row.description,
        "discount_type": row.discount_type,
        "value": row.value,
        "max_discount": row.max_discount,
        "duration": row.duration,
        "starts_at": row.starts_at,
        "ends_at": row.ends_at,
        "usage_limit": row.usage_limit,
        "usage_count": row.usage_count,
        "is_active": row.is_active,
        "plan_ids": plan_ids,
        "scope": "PLANS" if plan_ids else "ALL_PLANS",
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def sync_billing_coupon_plans(db: Session, coupon: BillingCoupon, plan_ids: list[int]) -> list[int]:
    unique = sorted({int(plan_id) for plan_id in plan_ids if int(plan_id) > 0})
    if unique:
        rows = db.query(Plan.id).filter(Plan.id.in_(unique)).all()
        if len(rows) != len(unique):
            raise ValueError("Há planos inválidos no cupom")
    db.query(BillingCouponPlan).filter(BillingCouponPlan.coupon_id == coupon.id).delete(synchronize_session=False)
    now = utcnow()
    for plan_id in unique:
        db.add(BillingCouponPlan(coupon_id=coupon.id, plan_id=plan_id, created_at=now))
    return unique


def _billing_coupon_window_active(coupon: BillingCoupon, now: datetime | None = None) -> bool:
    now = aware(now) or utcnow()
    start = aware(coupon.starts_at)
    end = aware(coupon.ends_at)
    return not ((start and start > now) or (end and end < now))


def validate_billing_coupon(
    db: Session,
    code: str | None,
    *,
    plan: Plan,
    billing_cycle: str,
    amount: Decimal | None = None,
    now: datetime | None = None,
) -> tuple[BillingCoupon | None, Decimal, Decimal]:
    subtotal = amount_for_plan(plan, billing_cycle) if amount is None else Decimal(amount).quantize(Decimal("0.01"))
    if not code:
        return None, Decimal("0.00"), subtotal
    normalized = code.strip().upper().replace(" ", "")
    coupon = db.query(BillingCoupon).filter(BillingCoupon.code == normalized).first()
    if not coupon or not coupon.is_active or not _billing_coupon_window_active(coupon, now):
        raise ValueError("Cupom de plano inválido ou expirado")
    if coupon.usage_limit is not None and int(coupon.usage_count or 0) >= int(coupon.usage_limit):
        raise ValueError("Este cupom de plano atingiu o limite de usos")
    plan_ids = [row.plan_id for row in db.query(BillingCouponPlan).filter(BillingCouponPlan.coupon_id == coupon.id).all()]
    if plan_ids and plan.id not in plan_ids:
        raise ValueError("Este cupom não é válido para o plano escolhido")
    if coupon.discount_type == "PERCENT":
        if Decimal(coupon.value) > 100:
            raise ValueError("Percentual do cupom não pode ultrapassar 100%")
        discount = subtotal * (Decimal(coupon.value) / Decimal("100"))
    elif coupon.discount_type == "FIXED":
        discount = Decimal(coupon.value)
    else:
        raise ValueError("Tipo de cupom inválido")
    if coupon.max_discount is not None:
        discount = min(discount, Decimal(coupon.max_discount))
    discount = min(max(discount, Decimal("0.00")), subtotal).quantize(Decimal("0.01"))
    total = max(Decimal("0.00"), subtotal - discount).quantize(Decimal("0.01"))
    return coupon, discount, total


def _invoice_dict(row: SubscriptionInvoice) -> dict:
    return {
        "id": row.id,
        "store_id": row.store_id,
        "store_name": row.store.name if row.store else None,
        "subscription_id": row.subscription_id,
        "plan_id": row.plan_id,
        "plan_name": row.plan.name if row.plan else None,
        "provider": row.provider,
        "status": row.status,
        "invoice_type": row.invoice_type,
        "billing_cycle": row.billing_cycle,
        "subtotal_amount": row.subtotal_amount if row.subtotal_amount is not None else row.amount,
        "discount_amount": row.discount_amount or Decimal("0.00"),
        "amount": row.amount,
        "currency": row.currency,
        "billing_coupon_id": row.billing_coupon_id,
        "coupon_code": row.coupon_code,
        "payment_method": row.payment_method,
        "provider_status": row.provider_status,
        "external_payment_id": row.external_payment_id,
        "checkout_url": row.checkout_url,
        "pix_available": bool(row.pix_qr_code),
        "pix_expires_at": row.pix_expires_at,
        "due_at": row.due_at,
        "period_start": row.period_start,
        "period_end": row.period_end,
        "paid_at": row.paid_at,
        "failed_at": row.failed_at,
        "failure_reason": row.failure_reason,
        "attempt_count": row.attempt_count,
        "last_attempt_at": row.last_attempt_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
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


def invoice_dict(row: SubscriptionInvoice) -> dict:
    return _invoice_dict(row)


def admin_billing_overview(db: Session, store_id: int) -> dict:
    invoices = (
        db.query(SubscriptionInvoice)
        .options(selectinload(SubscriptionInvoice.plan), selectinload(SubscriptionInvoice.store))
        .filter(SubscriptionInvoice.store_id == store_id)
        .order_by(SubscriptionInvoice.created_at.desc(), SubscriptionInvoice.id.desc())
        .limit(20)
        .all()
    )
    context = plan_context(db, store_id)
    plan_grace = (context.get("plan") or {}).get("grace_days")
    return {
        "subscription": context,
        "providers": provider_statuses(),
        "billing_policy": {
            "currency": settings.billing_default_currency,
            "invoice_lead_days": settings.billing_invoice_lead_days,
            "grace_days": settings.billing_grace_days if plan_grace is None else plan_grace,
        },
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


def list_invoices(
    db: Session,
    *,
    store_id: int | None = None,
    invoice_status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    query = db.query(SubscriptionInvoice).options(
        selectinload(SubscriptionInvoice.plan),
        selectinload(SubscriptionInvoice.store),
    )
    if store_id is not None:
        query = query.filter(SubscriptionInvoice.store_id == store_id)
    if invoice_status:
        query = query.filter(SubscriptionInvoice.status == invoice_status.strip().upper())
    rows = query.order_by(SubscriptionInvoice.created_at.desc(), SubscriptionInvoice.id.desc()).limit(limit).all()
    return [_invoice_dict(row) for row in rows]


def ensure_plan(db: Session, plan_id: int) -> Plan | None:
    return db.query(Plan).filter(Plan.id == plan_id).first()


def gateway_price_dict(row: BillingGatewayPrice) -> dict:
    return _gateway_price_dict(row)


def get_store_subscription(db: Session, store_id: int) -> Subscription | None:
    active = (
        db.query(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.store))
        .filter(Subscription.store_id == store_id, Subscription.status.in_(list(ACTIVE_OR_COLLECTIBLE)))
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .first()
    )
    if active:
        return active
    return (
        db.query(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.store))
        .filter(Subscription.store_id == store_id)
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .first()
    )


def get_subscription(db: Session, subscription_id: int) -> Subscription | None:
    return (
        db.query(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.store))
        .filter(Subscription.id == subscription_id)
        .first()
    )


def get_invoice(db: Session, invoice_id: int) -> SubscriptionInvoice | None:
    return (
        db.query(SubscriptionInvoice)
        .options(
            selectinload(SubscriptionInvoice.plan),
            selectinload(SubscriptionInvoice.store),
            selectinload(SubscriptionInvoice.subscription),
        )
        .filter(SubscriptionInvoice.id == invoice_id)
        .first()
    )


def _renewal_period(subscription: Subscription, now: datetime) -> tuple[datetime, datetime]:
    current_end = aware(subscription.current_period_end)
    start = current_end if current_end and current_end > now else now
    end = add_billing_cycle(start, subscription.billing_cycle)
    return start, end


def create_renewal_invoice(
    db: Session,
    subscription: Subscription,
    *,
    due_at: datetime | None = None,
    payment_method: str | None = None,
    now: datetime | None = None,
) -> tuple[SubscriptionInvoice, bool]:
    now = aware(now) or utcnow()
    if not subscription.plan:
        subscription = get_subscription(db, subscription.id) or subscription
    if not subscription.plan:
        raise ValueError("Assinatura sem plano associado")
    if subscription.status not in ACTIVE_OR_COLLECTIBLE:
        raise ValueError("A assinatura não está em estado cobravel")

    subtotal_amount = amount_for_subscription(subscription, subscription.billing_cycle)
    if subtotal_amount <= 0:
        raise ValueError("Plano gratuito não exige fatura de renovação")

    coupon = None
    discount_amount = Decimal("0.00")
    amount = subtotal_amount
    if subscription.billing_coupon_id:
        recurring_coupon = db.query(BillingCoupon).filter(BillingCoupon.id == subscription.billing_coupon_id).first()
        if recurring_coupon and recurring_coupon.duration == "RECURRING":
            try:
                coupon, discount_amount, amount = validate_billing_coupon(
                    db, recurring_coupon.code, plan=subscription.plan, billing_cycle=subscription.billing_cycle, amount=subtotal_amount, now=now
                )
            except ValueError:
                subscription.billing_coupon_id = None
        else:
            subscription.billing_coupon_id = None

    period_start, period_end = _renewal_period(subscription, now)
    existing = (
        db.query(SubscriptionInvoice)
        .filter(
            SubscriptionInvoice.subscription_id == subscription.id,
            SubscriptionInvoice.plan_id == subscription.plan_id,
            SubscriptionInvoice.invoice_type == "RENEWAL",
            SubscriptionInvoice.period_start == period_start,
            SubscriptionInvoice.status.in_(list(OPEN_INVOICE_STATUSES)),
        )
        .order_by(SubscriptionInvoice.id.desc())
        .first()
    )
    if existing:
        return existing, False

    row = SubscriptionInvoice(
        store_id=subscription.store_id,
        subscription_id=subscription.id,
        plan_id=subscription.plan_id,
        provider=subscription.provider or "MANUAL",
        status="PENDING",
        invoice_type="RENEWAL",
        billing_cycle=subscription.billing_cycle,
        subtotal_amount=subtotal_amount,
        discount_amount=discount_amount,
        amount=amount,
        currency=settings.billing_default_currency,
        billing_coupon_id=coupon.id if coupon else None,
        coupon_code=coupon.code if coupon else None,
        payment_method=payment_method,
        due_at=aware(due_at) or period_start,
        period_start=period_start,
        period_end=period_end,
        attempt_count=0,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    return row, True


def create_plan_change_invoice(
    db: Session,
    subscription: Subscription,
    *,
    plan: Plan,
    billing_cycle: str,
    coupon_code: str | None = None,
    due_at: datetime | None = None,
    now: datetime | None = None,
) -> tuple[SubscriptionInvoice, bool]:
    now = aware(now) or utcnow()
    if subscription.status not in ACTIVE_OR_COLLECTIBLE:
        raise ValueError("A assinatura atual não permite troca de plano")
    if not plan.is_active:
        raise ValueError("O plano escolhido está inativo")

    cycle = billing_cycle.strip().upper()
    subtotal_amount = amount_for_plan(plan, cycle)
    coupon, discount_amount, amount = validate_billing_coupon(
        db, coupon_code, plan=plan, billing_cycle=cycle, amount=subtotal_amount, now=now
    )
    period_start = now
    period_end = add_billing_cycle(period_start, cycle)

    existing = (
        db.query(SubscriptionInvoice)
        .filter(
            SubscriptionInvoice.subscription_id == subscription.id,
            SubscriptionInvoice.plan_id == plan.id,
            SubscriptionInvoice.invoice_type == "PLAN_CHANGE",
            SubscriptionInvoice.billing_cycle == cycle,
            SubscriptionInvoice.status.in_(list(OPEN_INVOICE_STATUSES)),
        )
        .order_by(SubscriptionInvoice.id.desc())
        .first()
    )
    if existing:
        existing.subtotal_amount = subtotal_amount
        existing.discount_amount = discount_amount
        existing.amount = amount
        existing.billing_coupon_id = coupon.id if coupon else None
        existing.coupon_code = coupon.code if coupon else None
        existing.updated_at = now
        db.flush()
        return existing, False

    row = SubscriptionInvoice(
        store_id=subscription.store_id,
        subscription_id=subscription.id,
        plan_id=plan.id,
        provider="MANUAL",
        status="PENDING",
        invoice_type="PLAN_CHANGE",
        billing_cycle=cycle,
        subtotal_amount=subtotal_amount,
        discount_amount=discount_amount,
        amount=amount,
        currency=settings.billing_default_currency,
        billing_coupon_id=coupon.id if coupon else None,
        coupon_code=coupon.code if coupon else None,
        due_at=aware(due_at) or now,
        period_start=period_start,
        period_end=period_end,
        attempt_count=0,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    return row, True


def apply_invoice_status(
    db: Session,
    invoice: SubscriptionInvoice,
    *,
    new_status: str,
    payment_method: str | None = None,
    failure_reason: str | None = None,
    now: datetime | None = None,
) -> SubscriptionInvoice:
    now = aware(now) or utcnow()
    status = new_status.strip().upper()
    if status not in {"PENDING", "PAID", "FAILED", "CANCELED"}:
        raise ValueError("Status de fatura inválido")

    # Idempotência: repetir a confirmação de uma fatura já paga não renova duas vezes.
    if invoice.status == "PAID" and status == "PAID":
        return invoice
    if invoice.status == "PAID" and status != "PAID":
        raise ValueError("Uma fatura paga não pode voltar para outro status")

    if payment_method:
        invoice.payment_method = payment_method
    invoice.last_attempt_at = now
    invoice.attempt_count = int(invoice.attempt_count or 0) + 1
    invoice.updated_at = now

    subscription = invoice.subscription
    if not subscription and invoice.subscription_id:
        subscription = db.query(Subscription).filter(Subscription.id == invoice.subscription_id).first()

    if status == "PAID":
        if not subscription:
            raise ValueError("Fatura sem assinatura associada")
        if not invoice.plan_id:
            invoice.plan_id = subscription.plan_id

        start = now
        if invoice.invoice_type == "RENEWAL":
            current_end = aware(subscription.current_period_end)
            start = current_end if current_end and current_end > now else now
        end = add_billing_cycle(start, invoice.billing_cycle)

        invoice.status = "PAID"
        invoice.provider_status = invoice.provider_status or "approved"
        invoice.paid_at = now
        invoice.failed_at = None
        invoice.failure_reason = None
        invoice.period_start = start
        invoice.period_end = end

        applied_coupon = None
        if invoice.billing_coupon_id:
            applied_coupon = db.query(BillingCoupon).filter(BillingCoupon.id == invoice.billing_coupon_id).first()
            existing_usage = db.query(BillingCouponUsage.id).filter(
                BillingCouponUsage.coupon_id == invoice.billing_coupon_id,
                BillingCouponUsage.invoice_id == invoice.id,
            ).first()
            if applied_coupon and not existing_usage:
                if (
                    applied_coupon.usage_limit is not None
                    and int(applied_coupon.usage_count or 0) >= int(applied_coupon.usage_limit)
                ):
                    raise ValueError("Este cupom de plano atingiu o limite de usos antes da confirmação do pagamento")
                applied_coupon.usage_count = int(applied_coupon.usage_count or 0) + 1
                db.add(BillingCouponUsage(
                    coupon_id=applied_coupon.id,
                    store_id=invoice.store_id,
                    subscription_id=subscription.id,
                    invoice_id=invoice.id,
                    discount_amount=invoice.discount_amount or Decimal("0.00"),
                    created_at=now,
                ))

        subscription.plan_id = invoice.plan_id or subscription.plan_id
        target_plan = invoice.plan or db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        if target_plan and (invoice.invoice_type == "PLAN_CHANGE" or subscription.commercial_terms_at is None):
            snapshot_subscription_terms(subscription, target_plan, now=now)
        subscription.billing_cycle = invoice.billing_cycle
        subscription.status = "ACTIVE"
        subscription.current_period_start = start
        subscription.current_period_end = end
        subscription.trial_ends_at = None
        subscription.canceled_at = None
        subscription.provider = invoice.provider or subscription.provider or "MANUAL"
        subscription.provider_status = "PAID"
        subscription.cancel_at_period_end = False
        subscription.next_billing_at = end
        if invoice.invoice_type == "PLAN_CHANGE":
            subscription.billing_coupon_id = (
                applied_coupon.id if applied_coupon and applied_coupon.duration == "RECURRING" else None
            )
        subscription.updated_at = now

    elif status == "FAILED":
        invoice.status = "FAILED"
        invoice.provider_status = invoice.provider_status or "rejected"
        invoice.failed_at = now
        invoice.failure_reason = failure_reason or "Pagamento não confirmado"
        if subscription and invoice.invoice_type == "RENEWAL":
            current_end = aware(subscription.current_period_end)
            if current_end and current_end <= now:
                subscription.status = "PAST_DUE"
                subscription.provider_status = "PAYMENT_FAILED"
                subscription.updated_at = now

    elif status == "CANCELED":
        invoice.status = "CANCELED"
        invoice.provider_status = invoice.provider_status or "cancelled"
        invoice.failure_reason = failure_reason

    else:  # PENDING, útil para reabrir uma tentativa manual que falhou.
        invoice.status = "PENDING"
        invoice.failed_at = None
        invoice.failure_reason = None

    db.flush()
    return invoice


def cancel_subscription(
    subscription: Subscription,
    *,
    at_period_end: bool,
    now: datetime | None = None,
) -> Subscription:
    now = aware(now) or utcnow()
    if subscription.status in {"CANCELED", "EXPIRED"}:
        return subscription

    if at_period_end and aware(subscription.current_period_end) and aware(subscription.current_period_end) > now:
        subscription.cancel_at_period_end = True
        subscription.auto_renew = False
        subscription.provider_status = "CANCEL_AT_PERIOD_END"
    else:
        subscription.status = "CANCELED"
        subscription.canceled_at = now
        subscription.cancel_at_period_end = False
        subscription.auto_renew = False
        subscription.next_billing_at = None
        subscription.provider_status = "CANCELED"
    subscription.updated_at = now
    return subscription


def process_due_billing(db: Session, *, now: datetime | None = None) -> dict:
    """Motor diário, seguro para repetição.

    - cria faturas de renovação antes do vencimento;
    - respeita cancelamento no fim do período;
    - mantém período de tolerância configurável;
    - expira assinatura após a tolerância;
    - renova planos gratuitos sem gerar cobrança.

    Nenhum gateway externo é chamado nesta fase.
    """
    now = aware(now) or utcnow()
    lead_until = now + timedelta(days=settings.billing_invoice_lead_days)

    stats = {
        "processed": 0,
        "invoices_created": 0,
        "past_due": 0,
        "expired": 0,
        "canceled": 0,
        "free_renewed": 0,
        "missing_period_end": 0,
    }

    rows = (
        db.query(Subscription)
        .options(selectinload(Subscription.plan))
        .filter(Subscription.status.in_(list(ACTIVE_OR_COLLECTIBLE)))
        .order_by(Subscription.id)
        .all()
    )

    for subscription in rows:
        stats["processed"] += 1
        period_end = aware(subscription.current_period_end)
        trial_end = aware(subscription.trial_ends_at) if subscription.status == "TRIAL" else None
        due_point = trial_end or period_end

        if due_point is None:
            stats["missing_period_end"] += 1
            continue

        if subscription.cancel_at_period_end and due_point <= now:
            subscription.status = "CANCELED"
            subscription.canceled_at = now
            subscription.next_billing_at = None
            subscription.provider_status = "CANCELED"
            subscription.updated_at = now
            stats["canceled"] += 1
            continue

        if not subscription.plan:
            continue

        try:
            amount = amount_for_subscription(subscription, subscription.billing_cycle)
        except ValueError:
            continue

        # Plano gratuito: não gera fatura; apenas abre o próximo período.
        if amount <= 0 and due_point <= now:
            start = now
            end = add_billing_cycle(start, subscription.billing_cycle)
            subscription.status = "ACTIVE"
            subscription.current_period_start = start
            subscription.current_period_end = end
            subscription.next_billing_at = end
            subscription.trial_ends_at = None
            subscription.provider_status = "FREE_RENEWAL"
            subscription.updated_at = now
            stats["free_renewed"] += 1
            continue

        # Fatura é gerada com antecedência, mas de forma idempotente.
        if amount > 0 and due_point <= lead_until:
            try:
                _invoice, created = create_renewal_invoice(db, subscription, due_at=due_point, now=now)
                if created:
                    stats["invoices_created"] += 1
            except ValueError:
                pass

        if due_point <= now:
            if subscription.status != "PAST_DUE":
                subscription.status = "PAST_DUE"
                subscription.provider_status = "AWAITING_PAYMENT"
                subscription.updated_at = now
                stats["past_due"] += 1
            grace_days = subscription.grace_days_snapshot
            if grace_days is None:
                grace_days = getattr(subscription.plan, "grace_days", settings.billing_grace_days)
            if due_point + timedelta(days=int(grace_days or 0)) <= now:
                subscription.status = "EXPIRED"
                subscription.provider_status = "EXPIRED"
                subscription.next_billing_at = None
                subscription.updated_at = now
                stats["expired"] += 1

    db.flush()
    return stats


def ensure_store(db: Session, store_id: int) -> Store | None:
    return db.query(Store).filter(Store.id == store_id).first()
