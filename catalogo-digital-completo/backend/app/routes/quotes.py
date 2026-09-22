from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.quotes import QuoteRequest
from ..models.store import Store
from ..repositories.catalog_repository import get_store_by_slug
from ..schemas.quotes import QuoteRequestCreate, QuoteResponseUpdate, QuoteStatusUpdate
from ..services.quote_service import (
    create_quote_request,
    get_quote_for_store,
    require_quotes_capability,
    respond_to_quote,
    update_quote_status,
)

public_router = APIRouter(prefix="/api/public", tags=["quotes-public"])
admin_router = APIRouter(prefix="/api/admin", tags=["quotes-admin"])


def _attachment_dict(item):
    return {
        "id": item.id,
        "file_name": item.file_name,
        "file_url": item.file_url,
        "mime_type": item.mime_type,
    }


def _quote_dict(quote: QuoteRequest, include_private: bool = True):
    result = {
        "id": quote.id if include_private else None,
        "public_token": quote.public_token,
        "service_id": quote.service_id,
        "service_name": quote.service.name if quote.service else None,
        "title": quote.title,
        "description": quote.description,
        "preferred_contact": quote.preferred_contact,
        "service_address": quote.service_address,
        "service_city": quote.service_city,
        "service_state": quote.service_state,
        "service_zip_code": quote.service_zip_code,
        "status": quote.status,
        "estimated_amount": quote.estimated_amount,
        "response_message": quote.response_message,
        "expires_at": quote.expires_at,
        "responded_at": quote.responded_at,
        "created_at": quote.created_at,
        "updated_at": quote.updated_at,
        "attachments": [_attachment_dict(x) for x in quote.attachments],
    }
    if include_private:
        result["customer"] = {
            "id": quote.customer.id if quote.customer else None,
            "name": quote.customer.name if quote.customer else None,
            "email": quote.customer.email if quote.customer else None,
            "phone": quote.customer.phone if quote.customer else None,
        }
    else:
        result.pop("id", None)
    return result


def _load_public_quote(db: Session, store_id: int, public_token: str) -> QuoteRequest:
    quote = db.query(QuoteRequest).options(
        selectinload(QuoteRequest.attachments),
        selectinload(QuoteRequest.service),
    ).filter(
        QuoteRequest.store_id == store_id,
        QuoteRequest.public_token == public_token,
    ).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Solicitação de orçamento não encontrada")
    return quote


@public_router.post("/stores/{slug}/quotes", status_code=201)
def create_public_quote(slug: str, payload: QuoteRequestCreate, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    quote = create_quote_request(db, store, payload)
    quote = _load_public_quote(db, store.id, quote.public_token)
    return _quote_dict(quote, include_private=False)


@public_router.get("/stores/{slug}/quotes/{public_token}")
def get_public_quote(slug: str, public_token: str, db: Session = Depends(get_db)):
    store = get_store_by_slug(db, slug)
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    require_quotes_capability(store)
    quote = _load_public_quote(db, store.id, public_token)
    return _quote_dict(quote, include_private=False)


@admin_router.get("/quotes")
def list_quotes(
    status: str | None = Query(default=None),
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id, Store.is_active.is_(True)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    require_quotes_capability(store)

    query = db.query(QuoteRequest).options(
        selectinload(QuoteRequest.attachments),
        selectinload(QuoteRequest.customer),
        selectinload(QuoteRequest.service),
    ).filter(QuoteRequest.store_id == store_id)
    if status:
        query = query.filter(QuoteRequest.status == status)
    rows = query.order_by(QuoteRequest.created_at.desc()).all()
    return [_quote_dict(x) for x in rows]


@admin_router.get("/quotes/{quote_id}")
def get_quote(
    quote_id: int,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    get_quote_for_store(db, store_id, quote_id)
    quote = db.query(QuoteRequest).options(
        selectinload(QuoteRequest.attachments),
        selectinload(QuoteRequest.customer),
        selectinload(QuoteRequest.service),
    ).filter(QuoteRequest.id == quote_id, QuoteRequest.store_id == store_id).one()
    return _quote_dict(quote)


@admin_router.patch("/quotes/{quote_id}/status")
def patch_quote_status(
    quote_id: int,
    payload: QuoteStatusUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id, Store.is_active.is_(True)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    require_quotes_capability(store)
    quote = get_quote_for_store(db, store_id, quote_id)
    quote = update_quote_status(db, quote, payload.status)
    return _quote_dict(quote)


@admin_router.put("/quotes/{quote_id}/response")
def put_quote_response(
    quote_id: int,
    payload: QuoteResponseUpdate,
    store_id: int = Depends(get_current_store_id),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id, Store.is_active.is_(True)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Loja não encontrada")
    require_quotes_capability(store)
    quote = get_quote_for_store(db, store_id, quote_id)
    quote = respond_to_quote(db, quote, payload)
    quote = db.query(QuoteRequest).options(
        selectinload(QuoteRequest.attachments),
        selectinload(QuoteRequest.customer),
        selectinload(QuoteRequest.service),
    ).filter(QuoteRequest.id == quote.id, QuoteRequest.store_id == store_id).one()
    return _quote_dict(quote)
