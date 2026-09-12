from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    yearly_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    limits: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    features: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", nullable=False, index=True)
    billing_cycle: Mapped[str] = mapped_column(String(16), default="MONTHLY", nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider: Mapped[str] = mapped_column(String(40), default="MANUAL", nullable=False)
    external_customer_id: Mapped[str | None] = mapped_column(String(160), index=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String(160), index=True)
    provider_status: Mapped[str | None] = mapped_column(String(60))
    external_plan_id: Mapped[str | None] = mapped_column(String(160))
    external_price_id: Mapped[str | None] = mapped_column(String(160))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    billing_coupon_id: Mapped[int | None] = mapped_column(ForeignKey("billing_coupons.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    store = relationship("Store", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
