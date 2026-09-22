from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.store import Store
from ..schemas.store import StoreUpdate
from ..services.subscription_service import plan_context

public_router = APIRouter(prefix="/api/public", tags=["stores-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["stores-admin"])


def _store_dict(store: Store):
    return {
        "id": store.id,
        "name": store.name,
        "slug": store.slug,
        "description": store.description,
        "logo_url": store.logo_url,
        "banner_url": store.banner_url,
        "panel_brand_name": store.panel_brand_name,
        "panel_logo_url": store.panel_logo_url,
        "primary_color": store.primary_color,
        "secondary_color": store.secondary_color,
        "whatsapp": store.whatsapp,
        "phone": store.phone,
        "email": store.email,
        "address": store.address,
        "city": store.city,
        "state": store.state,
        "zip_code": store.zip_code,
        "is_active": store.is_active,
        "capabilities": store.capabilities,
        "business_model": (
            {
                "id": store.business_model.id,
                "name": store.business_model.name,
                "code": store.business_model.code,
                "primary_action": store.business_model.primary_action,
            }
            if store.business_model
            else None
        ),
        "business_category": (
            {
                "id": store.business_category.id,
                "name": store.business_category.name,
                "slug": store.business_category.slug,
            }
            if store.business_category
            else None
        ),
    }


def _load_store(db: Session, store_id: int):
    return (
        db.query(Store)
        .options(selectinload(Store.business_model), selectinload(Store.business_category))
        .filter(Store.id == store_id, Store.is_active.is_(True))
        .first()
    )


@public_router.get("/stores/{slug}")
def public_store(slug: str, db: Session = Depends(get_db)):
    store = (
        db.query(Store)
        .options(selectinload(Store.business_model), selectinload(Store.business_category))
        .filter(Store.slug == slug, Store.is_active.is_(True))
        .first()
    )
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    return _store_dict(store)


@admin_router.get("/store")
def admin_store(
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    store = _load_store(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    data = _store_dict(store)
    data["subscription"] = plan_context(db, store_id)
    return data


@admin_router.patch("/store")
def update_admin_store(
    data: StoreUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    store = _load_store(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(store, key, value)
    db.commit()
    db.refresh(store)
    data = _store_dict(_load_store(db, store_id))
    data["subscription"] = plan_context(db, store_id)
    return data
