from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..billing.registry import provider_statuses
from ..database import get_db
from ..dependencies import get_current_store_id, get_current_super_admin
from ..models import BillingGatewayPrice, User
from ..schemas.billing import GatewayPriceCreate, GatewayPriceUpdate
from ..services.billing_service import (
    admin_billing_overview,
    ensure_plan,
    gateway_price_dict,
    list_gateway_prices,
)

admin_router = APIRouter(prefix="/api/admin/billing", tags=["subscription-billing-admin"])
super_router = APIRouter(prefix="/api/super-admin/billing", tags=["subscription-billing-super-admin"])


@admin_router.get("/providers")
def admin_billing_providers(
    _store_id: int = Depends(get_current_store_id),
):
    return provider_statuses()


@admin_router.get("/overview")
def billing_overview(
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    return admin_billing_overview(db, store_id)


@super_router.get("/providers")
def super_billing_providers(
    _super_admin: User = Depends(get_current_super_admin),
):
    return provider_statuses()


@super_router.get("/gateway-prices")
def super_list_gateway_prices(
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    return list_gateway_prices(db)


@super_router.post("/gateway-prices", status_code=status.HTTP_201_CREATED)
def super_create_gateway_price(
    data: GatewayPriceCreate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    plan = ensure_plan(db, data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    row = BillingGatewayPrice(**data.model_dump())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Já existe um preço para este plano, gateway, ciclo e moeda",
        )
    row = (
        db.query(BillingGatewayPrice)
        .options(selectinload(BillingGatewayPrice.plan))
        .filter(BillingGatewayPrice.id == row.id)
        .one()
    )
    return gateway_price_dict(row)


@super_router.patch("/gateway-prices/{gateway_price_id}")
def super_update_gateway_price(
    gateway_price_id: int,
    data: GatewayPriceUpdate,
    _super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BillingGatewayPrice).filter(BillingGatewayPrice.id == gateway_price_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Preço de gateway não encontrado")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    row = (
        db.query(BillingGatewayPrice)
        .options(selectinload(BillingGatewayPrice.plan))
        .filter(BillingGatewayPrice.id == gateway_price_id)
        .one()
    )
    return gateway_price_dict(row)
