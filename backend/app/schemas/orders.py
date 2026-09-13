from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, model_validator


class CheckoutCustomer(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class CheckoutItem(BaseModel):
    product_id: int
    variant_id: int | None = None
    selected_option_item_ids: list[int] = Field(default_factory=list)
    quantity: int = Field(ge=1, le=999)


class CheckoutRequest(BaseModel):
    customer: CheckoutCustomer
    items: list[CheckoutItem] = Field(min_length=1)
    payment_method: str = Field(pattern="^(PIX|PIX_ONLINE|DINHEIRO|CARTAO_ENTREGA|WHATSAPP)$")
    payment_document: str | None = Field(default=None, max_length=20)
    fulfillment_method: str = Field(default="RETIRADA", pattern="^(RETIRADA|ENTREGA)$")
    notes: str | None = Field(default=None, max_length=1000)
    delivery_address: str | None = Field(default=None, max_length=255)
    delivery_city: str | None = Field(default=None, max_length=120)
    delivery_state: str | None = Field(default=None, min_length=2, max_length=2)
    delivery_zip_code: str | None = Field(default=None, max_length=20)
    coupon_code: str | None = Field(default=None, max_length=40)

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


class OrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(PENDENTE|CONFIRMADO|EM_PREPARACAO|PRONTO|SAIU_PARA_ENTREGA|ENTREGUE|CANCELADO)$"
    )


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None
    variant_id: int | None
    product_name: str
    variant_name: str | None
    sku: str | None
    original_unit_price: Decimal | None = None
    unit_price: Decimal
    promotion_name: str | None = None
    selected_options: list[dict] = Field(default_factory=list)
    quantity: int
    line_total: Decimal


class OrderOut(BaseModel):
    id: int
    order_number: str
    status: str
    payment_method: str
    fulfillment_method: str
    subtotal: Decimal
    discount_amount: Decimal
    coupon_code: str | None = None
    delivery_fee: Decimal
    total: Decimal
    notes: str | None
    customer: dict | None
    items: list[OrderItemOut]
    created_at: str
