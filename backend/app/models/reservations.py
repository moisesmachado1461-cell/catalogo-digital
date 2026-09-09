from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (
        UniqueConstraint("store_id", "slug", name="uq_resources_store_slug"),
        CheckConstraint("capacity > 0", name="ck_resources_capacity_positive"),
        CheckConstraint("price_per_day >= 0", name="ck_resources_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    resource_type: Mapped[str] = mapped_column(String(60), default="RECURSO", nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_per_day: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    store = relationship("Store", back_populates="resources")
    reservations = relationship("Reservation", back_populates="resource")


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_reservations_time_order"),
        CheckConstraint("guests > 0", name="ck_reservations_guests_positive"),
        CheckConstraint("total >= 0", name="ck_reservations_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_token: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    guests: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDENTE", nullable=False, index=True)
    daily_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    store = relationship("Store", back_populates="reservations")
    customer = relationship("Customer", back_populates="reservations")
    resource = relationship("Resource", back_populates="reservations")


class RentalItem(Base):
    __tablename__ = "rental_items"
    __table_args__ = (
        UniqueConstraint("store_id", "slug", name="uq_rental_items_store_slug"),
        UniqueConstraint("store_id", "sku", name="uq_rental_items_store_sku"),
        CheckConstraint("daily_rate >= 0", name="ck_rental_items_rate_nonnegative"),
        CheckConstraint("deposit_amount >= 0", name="ck_rental_items_deposit_nonnegative"),
        CheckConstraint("quantity_total > 0", name="ck_rental_items_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sku: Mapped[str | None] = mapped_column(String(80))
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_total: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    store = relationship("Store", back_populates="rental_items")
    rentals = relationship("RentalReservation", back_populates="item")


class RentalReservation(Base):
    __tablename__ = "rental_reservations"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_rental_reservations_time_order"),
        CheckConstraint("quantity > 0", name="ck_rental_reservations_quantity_positive"),
        CheckConstraint("rental_days > 0", name="ck_rental_reservations_days_positive"),
        CheckConstraint("daily_rate_snapshot >= 0", name="ck_rental_reservations_rate_nonnegative"),
        CheckConstraint("deposit_amount >= 0", name="ck_rental_reservations_deposit_nonnegative"),
        CheckConstraint("total >= 0", name="ck_rental_reservations_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_token: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    rental_item_id: Mapped[int] = mapped_column(ForeignKey("rental_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    rental_days: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDENTE", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    store = relationship("Store", back_populates="rental_reservations")
    customer = relationship("Customer", back_populates="rental_reservations")
    item = relationship("RentalItem", back_populates="rentals")
