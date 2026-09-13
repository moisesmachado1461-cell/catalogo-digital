from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.payments import Payment, PaymentSettings
from ..models.store import Store
from ..repositories.catalog_repository import get_store_by_slug
from ..schemas.payments import PaymentSettingsUpdate, PaymentStatusUpdate
from ..services.payment_service import (
    available_payment_options,
    get_settings_row,
    payment_dict,
    payment_settings_dict,
    update_payment_status,
)

public_router = APIRouter(prefix="/api/public", tags=["payments-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["payments-admin"])


def _admin_store(db: Session, store_id: int) -> Store:
    store = db.query(Store).filter(Store.id == store_id, Store.is_active.is_(True)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    return store


@public_router.get("/stores/{slug}/payment-options")
def public_payment_options(slug: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    return {"store_id": store.id, "options": available_payment_options(db, store)}


@public_router.get("/stores/{slug}/payments/{token}")
def public_payment(slug: str, token: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    row = db.query(Payment).filter(Payment.store_id == store.id, Payment.public_token == token).first()
    if not row:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment_dict(row)


@admin_router.get("/payment-settings")
def admin_payment_settings(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    _admin_store(db, store_id)
    return payment_settings_dict(get_settings_row(db, store_id), store_id)


@admin_router.patch("/payment-settings")
def update_admin_payment_settings(
    data: PaymentSettingsUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    store = _admin_store(db, store_id)
    if not store.capabilities.get("payments", False):
        raise HTTPException(status_code=403, detail="Pagamentos não estão habilitados para esta empresa")
    row = get_settings_row(db, store_id)
    if not row:
        row = PaymentSettings(store_id=store_id)
        db.add(row)
    values = data.model_dump()
    for key, value in values.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(row, key, value)
    row.online_gateway = "NONE"
    row.is_active = True
    db.commit()
    db.refresh(row)
    return payment_settings_dict(row, store_id)


@admin_router.get("/payments")
def admin_payments(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    _admin_store(db, store_id)
    rows = db.query(Payment).filter(Payment.store_id == store_id).order_by(Payment.created_at.desc()).all()
    return [payment_dict(row) for row in rows]


@admin_router.patch("/payments/{payment_id}/status")
def admin_payment_status(
    payment_id: int,
    data: PaymentStatusUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    _admin_store(db, store_id)
    row = db.query(Payment).filter(Payment.id == payment_id, Payment.store_id == store_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment_dict(update_payment_status(db, row, data.status))
