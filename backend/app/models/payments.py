from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentSettings(Base):
    __tablename__ = "payment_settings"
    __table_args__ = (UniqueConstraint("store_id", name="uq_payment_settings_store"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pix_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pix_key_type: Mapped[str | None] = mapped_column(String(20))
    pix_key: Mapped[str | None] = mapped_column(String(255))
    pix_receiver_name: Mapped[str | None] = mapped_column(String(160))
    pix_receiver_city: Mapped[str | None] = mapped_column(String(120))
    cash_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    card_on_delivery_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    online_gateway: Mapped[str] = mapped_column(String(40), default="NONE", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    store = relationship("Store", back_populates="payment_settings")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("store_id", "reference_type", "reference_id", name="uq_payments_store_reference"),
        CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_token: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reference_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="MANUAL", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDENTE", nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    pix_key_type_snapshot: Mapped[str | None] = mapped_column(String(20))
    pix_key_snapshot: Mapped[str | None] = mapped_column(String(255))
    pix_receiver_name_snapshot: Mapped[str | None] = mapped_column(String(160))
    pix_receiver_city_snapshot: Mapped[str | None] = mapped_column(String(120))
    instructions: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(String(160), index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    store = relationship("Store", back_populates="payments")
