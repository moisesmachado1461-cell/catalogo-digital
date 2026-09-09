from pydantic import BaseModel, EmailStr, Field, field_validator


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=3000)
    logo_url: str | None = Field(default=None, max_length=500)
    banner_url: str | None = Field(default=None, max_length=500)
    primary_color: str | None = Field(default=None, max_length=20)
    secondary_color: str | None = Field(default=None, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    zip_code: str | None = Field(default=None, max_length=20)

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, value: str | None):
        if value is None or value == "":
            return value
        if len(value) not in (4, 7) or not value.startswith("#"):
            raise ValueError("A cor deve estar no formato hexadecimal, por exemplo #7C3AED")
        chars = value[1:]
        if any(ch not in "0123456789abcdefABCDEF" for ch in chars):
            raise ValueError("A cor deve estar no formato hexadecimal")
        return value.upper()

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str | None):
        return value.upper() if value else value
