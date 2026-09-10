from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from ..billing.registry import PROVIDER_CATALOG, normalize_provider


class GatewayPriceCreate(BaseModel):
    plan_id: int = Field(gt=0)
    provider: str = Field(min_length=2, max_length=40)
    billing_cycle: str = "MONTHLY"
    currency: str = "BRL"
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    external_plan_id: str | None = Field(default=None, max_length=160)
    external_price_id: str | None = Field(default=None, max_length=160)
    is_active: bool = True

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str):
        code = normalize_provider(value)
        if code not in PROVIDER_CATALOG:
            raise ValueError(f"provider deve ser um de: {', '.join(PROVIDER_CATALOG)}")
        return code

    @field_validator("billing_cycle")
    @classmethod
    def validate_cycle(cls, value: str):
        value = value.strip().upper()
        if value not in {"MONTHLY", "YEARLY"}:
            raise ValueError("billing_cycle deve ser MONTHLY ou YEARLY")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str):
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency deve usar código ISO de 3 letras, por exemplo BRL")
        return value


class GatewayPriceUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    external_plan_id: str | None = Field(default=None, max_length=160)
    external_price_id: str | None = Field(default=None, max_length=160)
    is_active: bool | None = None


class RenewalInvoiceCreate(BaseModel):
    due_at: datetime | None = None
    payment_method: str | None = Field(default=None, max_length=40)


class PlanChangeInvoiceCreate(BaseModel):
    plan_id: int = Field(gt=0)
    billing_cycle: str = "MONTHLY"
    due_at: datetime | None = None

    @field_validator("billing_cycle")
    @classmethod
    def validate_cycle(cls, value: str):
        value = value.strip().upper()
        if value not in {"MONTHLY", "YEARLY"}:
            raise ValueError("billing_cycle deve ser MONTHLY ou YEARLY")
        return value


class InvoiceStatusUpdate(BaseModel):
    status: str
    payment_method: str | None = Field(default=None, max_length=40)
    failure_reason: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        value = value.strip().upper()
        allowed = {"PENDING", "PAID", "FAILED", "CANCELED"}
        if value not in allowed:
            raise ValueError(f"status deve ser um de: {', '.join(sorted(allowed))}")
        return value


class SubscriptionCancelRequest(BaseModel):
    at_period_end: bool = True
