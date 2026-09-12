from pydantic import BaseModel, EmailStr, Field, field_validator


class SuperAdminStoreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    business_category_id: int
    description: str | None = Field(default=None, max_length=3000)
    primary_color: str = Field(default="#7C3AED", max_length=20)
    secondary_color: str = Field(default="#4F46E5", max_length=20)
    whatsapp: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    zip_code: str | None = Field(default=None, max_length=20)
    admin_name: str = Field(min_length=2, max_length=120)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)
    plan_id: int | None = None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, value: str):
        if len(value) not in (4, 7) or not value.startswith("#"):
            raise ValueError("A cor deve estar em hexadecimal, por exemplo #7C3AED")
        if any(ch not in "0123456789abcdefABCDEF" for ch in value[1:]):
            raise ValueError("A cor deve estar em hexadecimal")
        return value.upper()

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str | None):
        return value.upper() if value else value



class SuperAdminStoreUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    business_category_id: int
    description: str | None = Field(default=None, max_length=3000)
    primary_color: str = Field(default="#7C3AED", max_length=20)
    secondary_color: str = Field(default="#4F46E5", max_length=20)
    whatsapp: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    zip_code: str | None = Field(default=None, max_length=20)
    admin_name: str | None = Field(default=None, min_length=2, max_length=120)
    admin_email: EmailStr | None = None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, value: str):
        if len(value) not in (4, 7) or not value.startswith("#"):
            raise ValueError("A cor deve estar em hexadecimal, por exemplo #7C3AED")
        if any(ch not in "0123456789abcdefABCDEF" for ch in value[1:]):
            raise ValueError("A cor deve estar em hexadecimal")
        return value.upper()

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str | None):
        return value.upper() if value else value


class StoreStatusUpdate(BaseModel):
    is_active: bool


class SuperAdminProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    current_password: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str):
        value = " ".join(value.strip().split())
        if len(value) < 2:
            raise ValueError("Informe um nome válido")
        return value


class SuperAdminPasswordUpdate(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no máximo 72 bytes")
        checks = [
            any(ch.islower() for ch in value),
            any(ch.isupper() for ch in value),
            any(ch.isdigit() for ch in value),
            any(not ch.isalnum() for ch in value),
        ]
        if not all(checks):
            raise ValueError("Use maiúscula, minúscula, número e símbolo na nova senha")
        return value


class SuperAdminSessionRevoke(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
