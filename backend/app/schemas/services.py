from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    category_id: int | None = None
    description: str | None = None
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    duration_minutes: int = Field(ge=5, le=1440)
    image_url: str | None = Field(default=None, max_length=500)


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    category_id: int | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    duration_minutes: int | None = Field(default=None, ge=5, le=1440)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ProfessionalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    image_url: str | None = Field(default=None, max_length=500)


class ProfessionalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ProfessionalServicesUpdate(BaseModel):
    service_ids: list[int] = Field(default_factory=list)

    @field_validator("service_ids")
    @classmethod
    def unique_service_ids(cls, value: list[int]):
        if len(value) != len(set(value)):
            raise ValueError("service_ids não pode conter valores duplicados")
        return value


class ProfessionalHourInput(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_active: bool = True

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, value: time, info):
        start = info.data.get("start_time")
        if start is not None and value <= start:
            raise ValueError("end_time deve ser maior que start_time")
        return value


class ProfessionalHoursUpdate(BaseModel):
    hours: list[ProfessionalHourInput] = Field(default_factory=list, max_length=7)

    @field_validator("hours")
    @classmethod
    def unique_days(cls, value: list[ProfessionalHourInput]):
        days = [item.day_of_week for item in value]
        if len(days) != len(set(days)):
            raise ValueError("Cada day_of_week pode aparecer apenas uma vez")
        return value


class AppointmentCustomer(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class AppointmentCreate(BaseModel):
    customer: AppointmentCustomer
    service_id: int
    professional_id: int
    starts_at: datetime
    payment_method: str | None = Field(default=None, pattern="^(PIX|PIX_ONLINE|DINHEIRO|CARTAO_ENTREGA|WHATSAPP)$")
    payment_document: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_online_pix(self):
        if self.payment_method == "PIX_ONLINE":
            if not self.customer.email:
                raise ValueError("Pix online exige e-mail do cliente")
            digits = "".join(ch for ch in (self.payment_document or "") if ch.isdigit())
            if len(digits) not in {11, 14}:
                raise ValueError("Pix online exige CPF ou CNPJ válido")
            self.payment_document = digits
        return self

    @field_validator("starts_at")
    @classmethod
    def require_timezone(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("starts_at deve incluir fuso horário, por exemplo -03:00")
        return value


class AppointmentStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(PENDENTE|CONFIRMADO|CONCLUIDO|CANCELADO|NAO_COMPARECEU)$"
    )

class ProfessionalBlockCreate(BaseModel):
    professional_id: int
    starts_at: datetime
    ends_at: datetime
    reason: str | None = Field(default=None, max_length=255)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_block_timezone(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Data/hora deve incluir fuso horário")
        return value

    @field_validator("ends_at")
    @classmethod
    def validate_block_order(cls, value: datetime, info):
        start = info.data.get("starts_at")
        if start and value <= start:
            raise ValueError("ends_at deve ser posterior a starts_at")
        return value
