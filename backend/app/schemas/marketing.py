from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


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
    is_public: bool = False
    product_ids: list[int] = Field(default_factory=list)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "")
        if not all(ch.isalnum() or ch in "-_" for ch in normalized):
            raise ValueError("Use apenas letras, números, hífen ou sublinhado no código")
        return normalized

    @model_validator(mode="after")
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("A data final do cupom deve ser posterior à data inicial")
        self.product_ids = sorted({int(product_id) for product_id in self.product_ids if int(product_id) > 0})
        return self


class CouponUpdate(CouponCreate):
    pass


class CouponPreviewItem(BaseModel):
    product_id: int = Field(gt=0)
    line_total: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class CouponPreviewRequest(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    subtotal: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    items: list[CouponPreviewItem] = Field(min_length=1, max_length=200)

    @field_validator("code")
    @classmethod
    def normalize_preview_code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "")


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
