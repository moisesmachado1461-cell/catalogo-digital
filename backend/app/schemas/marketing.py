from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class CouponCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    description: str | None = None
    discount_type: str = Field(pattern="^(PERCENT|FIXED)$")
    value: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    min_order_value: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    max_discount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    usage_limit: int | None = Field(default=None, ge=1)
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "")


class CouponUpdate(CouponCreate):
    pass


class PromotionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    discount_type: str = Field(pattern="^(PERCENT|FIXED)$")
    value: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    product_ids: list[int] = Field(min_length=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True


class PromotionUpdate(PromotionCreate):
    pass
