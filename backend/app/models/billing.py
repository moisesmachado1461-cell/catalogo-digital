from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BillingCoupon(Base):
    """Cupom comercial do SaaS, separado dos cupons de pedidos das lojas."""

    __tablename__ = "billing_coupons"
    __table_args__ = (
        CheckConstraint("value >= 0", name="ck_billing_coupons_value_nonnegative"),
        CheckConstraint("max_discount IS NULL OR max_discount >= 0", name="ck_billing_coupons_max_discount_nonnegative"),
        CheckConstraint("usage_limit IS NULL OR usage_limit >= 1", name="ck_billing_coupons_usage_limit_positive"),
        CheckConstraint("usage_count >= 0", name="ck_billing_coupons_usage_count_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(String(16), nullable=False, default="PERCENT")
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    duration: Mapped[str] = mapped_column(String(20), nullable=False, default="FIRST_INVOICE")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class BillingCouponPlan(Base):
    __tablename__ = "billing_coupon_plans"
    __table_args__ = (UniqueConstraint("coupon_id", "plan_id", name="uq_billing_coupon_plan"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("billing_coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class BillingCouponUsage(Base):
    __tablename__ = "billing_coupon_usages"
    __table_args__ = (UniqueConstraint("coupon_id", "invoice_id", name="uq_billing_coupon_usage_invoice"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("billing_coupons.id", ondelete="RESTRICT"), nullable=False, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id", ondelete="SET NULL"), index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("subscription_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class BillingGatewayPrice(Base):
    """Mapeia um plano interno para o identificador/preço de um gateway externo."""

    __tablename__ = "billing_gateway_prices"
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "provider",
            "billing_cycle",
            "currency",
            name="uq_billing_gateway_price_plan_provider_cycle_currency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    billing_cycle: Mapped[str] = mapped_column(String(16), nullable=False, default="MONTHLY", index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    external_plan_id: Mapped[str | None] = mapped_column(String(160), index=True)
    external_price_id: Mapped[str | None] = mapped_column(String(160), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    plan = relationship("Plan")


class SubscriptionInvoice(Base):
    """Histórico financeiro da assinatura SaaS. Não é pagamento de pedido da loja."""

    __tablename__ = "subscription_invoices"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_invoice_id",
            name="uq_subscription_invoice_provider_external_invoice",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING", index=True)
    invoice_type: Mapped[str] = mapped_column(String(24), nullable=False, default="RENEWAL", index=True)
    billing_cycle: Mapped[str] = mapped_column(String(16), nullable=False, default="MONTHLY")
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    billing_coupon_id: Mapped[int | None] = mapped_column(ForeignKey("billing_coupons.id", ondelete="SET NULL"), index=True)
    coupon_code: Mapped[str | None] = mapped_column(String(40), index=True)
    external_invoice_id: Mapped[str | None] = mapped_column(String(160), index=True)
    external_payment_id: Mapped[str | None] = mapped_column(String(160), index=True)
    payment_method: Mapped[str | None] = mapped_column(String(40))
    checkout_url: Mapped[str | None] = mapped_column(String(700))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    store = relationship("Store")
    subscription = relationship("Subscription")
    plan = relationship("Plan")


class BillingWebhookEvent(Base):
    """Registro mínimo para idempotência/auditoria de webhooks de cobrança.

    O corpo bruto do webhook não é persistido; guardamos hash e metadados
    suficientes para deduplicação e diagnóstico sem copiar dados sensíveis.
    """

    __tablename__ = "billing_webhook_events"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_event_id",
            name="uq_billing_webhook_provider_external_event",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    external_event_id: Mapped[str | None] = mapped_column(String(190), index=True)
    event_type: Mapped[str | None] = mapped_column(String(120), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(190), index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="RECEIVED", index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
