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


class StoreStatusUpdate(BaseModel):
    is_active: bool
