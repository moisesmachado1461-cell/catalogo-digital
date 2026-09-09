from datetime import datetime, timezone
from secrets import token_urlsafe

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.quotes import QuoteAttachment, QuoteRequest
from ..models.sales import Customer
from ..models.services import Service
from ..models.store import Store
from ..schemas.quotes import QuoteRequestCreate, QuoteResponseUpdate


STATUS_TRANSITIONS = {
    "RECEBIDO": {"EM_ANALISE", "CANCELADO"},
    "EM_ANALISE": {"ORCAMENTO_ENVIADO", "CANCELADO"},
    "ORCAMENTO_ENVIADO": {"APROVADO", "RECUSADO", "CANCELADO"},
    "APROVADO": {"CONCLUIDO", "CANCELADO"},
    "RECUSADO": set(),
    "CANCELADO": set(),
    "CONCLUIDO": set(),
}


def require_quotes_capability(store: Store) -> None:
    if not store.capabilities.get("quotes", False):
        raise HTTPException(status_code=403, detail="Capability 'quotes' não habilitada para esta loja")


def _find_or_create_customer(db: Session, store_id: int, data) -> Customer:
    query = db.query(Customer).filter(Customer.store_id == store_id)
    customer = None
    if data.email:
        customer = query.filter(Customer.email == data.email.lower()).first()
    if not customer and data.phone:
        customer = db.query(Customer).filter(
            Customer.store_id == store_id,
            Customer.phone == data.phone,
        ).first()
    if not customer:
        customer = Customer(
            store_id=store_id,
            name=data.name,
            email=data.email.lower() if data.email else None,
            phone=data.phone,
            is_active=True,
        )
        db.add(customer)
        db.flush()
    else:
        customer.name = data.name
        if data.email:
            customer.email = data.email.lower()
        if data.phone:
            customer.phone = data.phone
    return customer


def create_quote_request(db: Session, store: Store, payload: QuoteRequestCreate) -> QuoteRequest:
    require_quotes_capability(store)

    service = None
    if payload.service_id is not None:
        service = db.query(Service).filter(
            Service.id == payload.service_id,
            Service.store_id == store.id,
            Service.is_active.is_(True),
        ).first()
        if not service:
            raise HTTPException(status_code=404, detail="Serviço não encontrado nesta loja")

    customer = _find_or_create_customer(db, store.id, payload.customer)
    token = token_urlsafe(24)
    while db.query(QuoteRequest).filter(QuoteRequest.public_token == token).first():
        token = token_urlsafe(24)

    quote = QuoteRequest(
        store_id=store.id,
        customer_id=customer.id,
        service_id=service.id if service else None,
        public_token=token,
        title=payload.title,
        description=payload.description,
        preferred_contact=payload.preferred_contact,
        service_address=payload.service_address,
        service_city=payload.service_city,
        service_state=payload.service_state,
        service_zip_code=payload.service_zip_code,
        status="RECEBIDO",
    )
    db.add(quote)
    db.flush()

    for item in payload.attachments:
        db.add(QuoteAttachment(
            store_id=store.id,
            quote_request_id=quote.id,
            file_name=item.file_name,
            file_url=item.file_url,
            mime_type=item.mime_type,
        ))

    db.commit()
    db.refresh(quote)
    return quote


def get_quote_for_store(db: Session, store_id: int, quote_id: int) -> QuoteRequest:
    quote = db.query(QuoteRequest).filter(
        QuoteRequest.id == quote_id,
        QuoteRequest.store_id == store_id,
    ).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Solicitação de orçamento não encontrada")
    return quote


def update_quote_status(db: Session, quote: QuoteRequest, new_status: str) -> QuoteRequest:
    if new_status == quote.status:
        return quote
    allowed = STATUS_TRANSITIONS.get(quote.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Transição de status inválida: {quote.status} -> {new_status}",
        )
    quote.status = new_status
    db.commit()
    db.refresh(quote)
    return quote


def respond_to_quote(db: Session, quote: QuoteRequest, payload: QuoteResponseUpdate) -> QuoteRequest:
    if quote.status not in {"RECEBIDO", "EM_ANALISE", "ORCAMENTO_ENVIADO"}:
        raise HTTPException(status_code=409, detail="Este orçamento não pode mais receber uma proposta")
    if payload.expires_at and payload.expires_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="expires_at deve incluir fuso horário")

    quote.estimated_amount = payload.estimated_amount
    quote.response_message = payload.response_message
    quote.expires_at = payload.expires_at
    quote.responded_at = datetime.now(timezone.utc)
    quote.status = "ORCAMENTO_ENVIADO"
    db.commit()
    db.refresh(quote)
    return quote
