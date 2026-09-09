from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class ResourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    description: str | None = None
    resource_type: str = Field(default="RECURSO", min_length=2, max_length=60)
    capacity: int = Field(default=1, ge=1, le=100000)
    price_per_day: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)


class ResourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    description: str | None = None
    resource_type: str | None = Field(default=None, min_length=2, max_length=60)
    capacity: int | None = Field(default=None, ge=1, le=100000)
    price_per_day: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ReservationCreate(BaseModel):
    customer: CustomerInput
    resource_id: int
    starts_at: datetime
    ends_at: datetime
    guests: int = Field(default=1, ge=1, le=100000)
    payment_method: str | None = Field(default=None, pattern="^(PIX|DINHEIRO|CARTAO_ENTREGA|WHATSAPP)$")
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def timezone_required(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Data/hora deve incluir fuso horário")
        return value

    @field_validator("ends_at")
    @classmethod
    def order_required(cls, value: datetime, info):
        start = info.data.get("starts_at")
        if start and value <= start:
            raise ValueError("ends_at deve ser posterior a starts_at")
        return value


class ReservationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(PENDENTE|CONFIRMADA|CONCLUIDA|CANCELADA)$")


class RentalItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    description: str | None = None
    sku: str | None = Field(default=None, max_length=80)
    daily_rate: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    deposit_amount: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    quantity_total: int = Field(default=1, ge=1, le=100000)
    image_url: str | None = Field(default=None, max_length=500)


class RentalItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    description: str | None = None
    sku: str | None = Field(default=None, max_length=80)
    daily_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    deposit_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    quantity_total: int | None = Field(default=None, ge=1, le=100000)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class RentalCreate(BaseModel):
    customer: CustomerInput
    rental_item_id: int
    starts_at: datetime
    ends_at: datetime
    quantity: int = Field(default=1, ge=1, le=100000)
    payment_method: str | None = Field(default=None, pattern="^(PIX|DINHEIRO|CARTAO_ENTREGA|WHATSAPP)$")
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def rental_timezone_required(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Data/hora deve incluir fuso horário")
        return value

    @field_validator("ends_at")
    @classmethod
    def rental_order_required(cls, value: datetime, info):
        start = info.data.get("starts_at")
        if start and value <= start:
            raise ValueError("ends_at deve ser posterior a starts_at")
        return value


class RentalStatusUpdate(BaseModel):
    status: str = Field(pattern="^(PENDENTE|CONFIRMADA|RETIRADA|DEVOLVIDA|CANCELADA)$")
