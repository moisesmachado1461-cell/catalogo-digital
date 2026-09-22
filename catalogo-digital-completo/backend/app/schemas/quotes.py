from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class QuoteCustomer(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class QuoteAttachmentInput(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_url: str = Field(min_length=1, max_length=1000)
    mime_type: str | None = Field(default=None, max_length=120)


class QuoteRequestCreate(BaseModel):
    customer: QuoteCustomer
    service_id: int | None = None
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=5000)
    preferred_contact: str = Field(default="WHATSAPP", pattern="^(WHATSAPP|PHONE|EMAIL)$")
    service_address: str | None = Field(default=None, max_length=255)
    service_city: str | None = Field(default=None, max_length=120)
    service_state: str | None = Field(default=None, min_length=2, max_length=2)
    service_zip_code: str | None = Field(default=None, max_length=20)
    attachments: list[QuoteAttachmentInput] = Field(default_factory=list, max_length=10)

    @field_validator("service_state")
    @classmethod
    def normalize_state(cls, value: str | None):
        return value.upper() if value else value


class QuoteStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(RECEBIDO|EM_ANALISE|ORCAMENTO_ENVIADO|APROVADO|RECUSADO|CANCELADO|CONCLUIDO)$"
    )


class QuoteResponseUpdate(BaseModel):
    estimated_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    response_message: str = Field(min_length=2, max_length=5000)
    expires_at: datetime | None = None
