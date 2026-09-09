from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    business_category_id: Mapped[int] = mapped_column(
        ForeignKey("business_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    business_model_id: Mapped[int] = mapped_column(
        ForeignKey("business_models.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    capabilities: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    banner_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str] = mapped_column(String(20), default="#7C3AED", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(20), default="#4F46E5", nullable=False)
    whatsapp: Mapped[str | None] = mapped_column(String(30))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(2))
    zip_code: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    business_category = relationship("BusinessCategory", back_populates="stores")
    business_model = relationship("BusinessModel", back_populates="stores")
    users = relationship("User", back_populates="store")
    catalog_categories = relationship("Category", back_populates="store")
    products = relationship("Product", back_populates="store")
    customers = relationship("Customer", back_populates="store")
    inventory_rows = relationship("Inventory", back_populates="store")
    orders = relationship("Order", back_populates="store")
    services = relationship("Service", back_populates="store")
    professionals = relationship("Professional", back_populates="store")
    appointments = relationship("Appointment", back_populates="store")
    quote_requests = relationship("QuoteRequest", back_populates="store")
    resources = relationship("Resource", back_populates="store")
    reservations = relationship("Reservation", back_populates="store")
    rental_items = relationship("RentalItem", back_populates="store")
    rental_reservations = relationship("RentalReservation", back_populates="store")
    payment_settings = relationship("PaymentSettings", back_populates="store", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="store")
    subscriptions = relationship("Subscription", back_populates="store")
