from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerRegisterRequest(BaseModel):
    store_slug: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=72)
    tracking_type: str | None = Field(default=None, pattern="^(ORDER|APPOINTMENT)$")
    tracking_token: str | None = Field(default=None, max_length=120)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if not any(ch.isalpha() for ch in value) or not any(ch.isdigit() for ch in value):
            raise ValueError("A senha deve ter letras e números")
        return value


class CustomerLoginRequest(BaseModel):
    store_slug: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class CustomerClaimRequest(BaseModel):
    tracking_type: str = Field(pattern="^(ORDER|APPOINTMENT)$")
    tracking_token: str = Field(min_length=8, max_length=120)
