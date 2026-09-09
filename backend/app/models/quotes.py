from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class QuoteRequest(Base):
    __tablename__ = "quote_requests"
    __table_args__ = (
        UniqueConstraint("public_token", name="uq_quote_requests_public_token"),
        CheckConstraint(
            "estimated_amount IS NULL OR estimated_amount >= 0",
            name="ck_quote_requests_estimated_amount_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"), index=True
    )
    public_token: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_contact: Mapped[str] = mapped_column(String(20), default="WHATSAPP", nullable=False)
    service_address: Mapped[str | None] = mapped_column(String(255))
    service_city: Mapped[str | None] = mapped_column(String(120))
    service_state: Mapped[str | None] = mapped_column(String(2))
    service_zip_code: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(32), default="RECEBIDO", nullable=False, index=True)
    estimated_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    response_message: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    store = relationship("Store", back_populates="quote_requests")
    customer = relationship("Customer", back_populates="quote_requests")
    service = relationship("Service")
    attachments = relationship(
        "QuoteAttachment", back_populates="quote_request", cascade="all, delete-orphan"
    )


class QuoteAttachment(Base):
    __tablename__ = "quote_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quote_request_id: Mapped[int] = mapped_column(
        ForeignKey("quote_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    quote_request = relationship("QuoteRequest", back_populates="attachments")
