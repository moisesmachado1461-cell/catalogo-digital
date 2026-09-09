from pydantic import BaseModel, EmailStr, Field, model_validator


class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(pattern="^(ACESSO|CORRECAO|EXCLUSAO|PORTABILIDADE|REVOGACAO)$")
    customer_name: str | None = Field(default=None, max_length=120)
    customer_email: EmailStr | None = None
    customer_phone: str | None = Field(default=None, max_length=40)
    details: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_contact(self):
        if not self.customer_email and not (self.customer_phone or "").strip():
            raise ValueError("Informe e-mail ou telefone para contato")
        return self


class PrivacyRequestUpdate(BaseModel):
    status: str = Field(pattern="^(PENDENTE|EM_ANALISE|CONCLUIDA|RECUSADA)$")
    admin_notes: str | None = Field(default=None, max_length=3000)
