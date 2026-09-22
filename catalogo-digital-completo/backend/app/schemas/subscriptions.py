from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class PlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    code: str = Field(min_length=2, max_length=40)
    description: str | None = None
    monthly_price: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    yearly_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    limits: dict = Field(default_factory=dict)
    features: dict = Field(default_factory=dict)
    is_active: bool = True
    sort_order: int = 0
    trial_days: int = Field(default=7, ge=0, le=90)
    grace_days: int = Field(default=5, ge=0, le=60)
    is_public: bool = True
    is_featured: bool = False
    badge: str | None = Field(default=None, max_length=60)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str):
        return value.strip().upper().replace(" ", "_")


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = None
    monthly_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    yearly_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    limits: dict | None = None
    features: dict | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    trial_days: int | None = Field(default=None, ge=0, le=90)
    grace_days: int | None = Field(default=None, ge=0, le=60)
    is_public: bool | None = None
    is_featured: bool | None = None
    badge: str | None = Field(default=None, max_length=60)


class StoreSubscriptionUpdate(BaseModel):
    plan_id: int
    status: str = "ACTIVE"
    billing_cycle: str = "MONTHLY"
    current_period_end: datetime | None = None
    trial_ends_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        value = value.upper()
        allowed = {"TRIAL", "ACTIVE", "PAST_DUE", "CANCELED", "EXPIRED"}
        if value not in allowed:
            raise ValueError(f"status deve ser um de: {', '.join(sorted(allowed))}")
        return value

    @field_validator("billing_cycle")
    @classmethod
    def validate_cycle(cls, value: str):
        value = value.upper()
        if value not in {"MONTHLY", "YEARLY"}:
            raise ValueError("billing_cycle deve ser MONTHLY ou YEARLY")
        return value
