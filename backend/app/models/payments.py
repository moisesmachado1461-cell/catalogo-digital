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
    provider_status: Mapped[str | None] = mapped_column(String(120))
    provider_idempotency_key: Mapped[str | None] = mapped_column(String(80), unique=True, index=True)
    pix_qr_code: Mapped[str | None] = mapped_column(Text)
    pix_qr_code_base64: Mapped[str | None] = mapped_column(Text)
    pix_ticket_url: Mapped[str | None] = mapped_column(Text)
    pix_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    store = relationship("Store", back_populates="payments")


class StorePaymentGatewayAccount(Base):
    __tablename__ = "store_payment_gateway_accounts"
    __table_args__ = (UniqueConstraint("store_id", "provider", name="uq_store_payment_gateway_account"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="MERCADO_PAGO", index=True)
    external_user_id: Mapped[str | None] = mapped_column(String(120), index=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scope: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CONNECTED", index=True)
    last_error: Mapped[str | None] = mapped_column(Text)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class StorePaymentOAuthState(Base):
    __tablename__ = "store_payment_oauth_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="MERCADO_PAGO", index=True)
    state_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    code_verifier_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
