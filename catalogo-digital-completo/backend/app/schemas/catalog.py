from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str | None
    image_url: str | None
    sort_order: int
    is_active: bool


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    category_id: int | None = None
    description: str | None = None
    sku: str | None = Field(default=None, max_length=80)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    compare_at_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    track_inventory: bool = True
    initial_stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=160)
    category_id: int | None = None
    description: str | None = None
    sku: str | None = Field(default=None, max_length=80)
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    compare_at_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    track_inventory: bool | None = None
    is_active: bool | None = None


class VariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sku: str | None = Field(default=None, max_length=80)
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    sort_order: int = 0
    initial_stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)


class VariantUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sku: str | None = Field(default=None, max_length=80)
    price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    sort_order: int = 0
    is_active: bool = True


class OptionItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_adjustment: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    sort_order: int = 0


class OptionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    required: bool = False
    min_selections: int = Field(default=0, ge=0)
    max_selections: int = Field(default=1, ge=1)
    sort_order: int = 0
    items: list[OptionItemCreate] = Field(default_factory=list)


class OptionUpdate(OptionCreate):
    is_active: bool = True


class InventoryOut(BaseModel):
    id: int
    product_id: int
    variant_id: int | None
    quantity: int
    reserved_quantity: int
    min_quantity: int


class InventoryUpdate(BaseModel):
    quantity: int = Field(ge=0)
    min_quantity: int | None = Field(default=None, ge=0)


class ProductOut(BaseModel):
    id: int
    category_id: int | None
    name: str
    slug: str
    description: str | None
    sku: str | None
    price: Decimal
    compare_at_price: Decimal | None
    image_url: str | None
    is_active: bool
    track_inventory: bool
    inventory: InventoryOut | None = None
    variants: list[dict] = Field(default_factory=list)
    options: list[dict] = Field(default_factory=list)
