from pydantic import BaseModel, Field, model_validator


class PaymentSettingsUpdate(BaseModel):
    pix_enabled: bool = False
    pix_key_type: str | None = Field(default=None, pattern="^(CPF|CNPJ|EMAIL|TELEFONE|ALEATORIA)$")
    pix_key: str | None = Field(default=None, max_length=255)
    pix_receiver_name: str | None = Field(default=None, max_length=160)
    pix_receiver_city: str | None = Field(default=None, max_length=120)
    cash_enabled: bool = True
    card_on_delivery_enabled: bool = True
    whatsapp_enabled: bool = True

    @model_validator(mode="after")
    def validate_pix(self):
        if self.pix_enabled:
            if not self.pix_key_type or not (self.pix_key or "").strip():
                raise ValueError("Para ativar PIX, informe o tipo e a chave")
            if not (self.pix_receiver_name or "").strip():
                raise ValueError("Para ativar PIX, informe o nome do recebedor")
        return self


class PaymentStatusUpdate(BaseModel):
    status: str = Field(pattern="^(PENDENTE|PAGO|RECUSADO|CANCELADO)$")
