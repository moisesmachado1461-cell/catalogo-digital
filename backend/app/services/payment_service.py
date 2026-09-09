from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.payments import Payment, PaymentSettings
from ..models.store import Store

CENT = Decimal("0.01")
PAYMENT_METHOD_LABELS = {
    "PIX": "PIX",
    "DINHEIRO": "Dinheiro",
    "CARTAO_ENTREGA": "Cartão no atendimento/entrega",
    "WHATSAPP": "Combinar pelo WhatsApp",
}
PAYMENT_TRANSITIONS = {
    "PENDENTE": {"PAGO", "RECUSADO", "CANCELADO"},
    "RECUSADO": {"PENDENTE", "CANCELADO"},
    "PAGO": set(),
    "CANCELADO": set(),
}


def money(value) -> Decimal:
    return Decimal(value or 0).quantize(CENT, rounding=ROUND_HALF_UP)


def default_settings_dict(store_id: int) -> dict:
    return {
        "id": None,
        "store_id": store_id,
        "pix_enabled": False,
        "pix_key_type": None,
        "pix_key": None,
        "pix_receiver_name": None,
        "pix_receiver_city": None,
        "cash_enabled": True,
        "card_on_delivery_enabled": True,
        "whatsapp_enabled": True,
        "online_gateway": "NONE",
        "is_active": True,
    }


def payment_settings_dict(row: PaymentSettings | None, store_id: int) -> dict:
    if row is None:
        return default_settings_dict(store_id)
    return {
        "id": row.id,
        "store_id": row.store_id,
        "pix_enabled": row.pix_enabled,
        "pix_key_type": row.pix_key_type,
        "pix_key": row.pix_key,
        "pix_receiver_name": row.pix_receiver_name,
        "pix_receiver_city": row.pix_receiver_city,
        "cash_enabled": row.cash_enabled,
        "card_on_delivery_enabled": row.card_on_delivery_enabled,
        "whatsapp_enabled": row.whatsapp_enabled,
        "online_gateway": row.online_gateway,
        "is_active": row.is_active,
    }


def get_settings_row(db: Session, store_id: int) -> PaymentSettings | None:
    return db.query(PaymentSettings).filter(PaymentSettings.store_id == store_id).first()


def available_payment_options(db: Session, store: Store) -> list[dict]:
    if not store.capabilities.get("payments", False):
        return []
    values = payment_settings_dict(get_settings_row(db, store.id), store.id)
    if not values["is_active"]:
        return []
    options = []
    if values["pix_enabled"] and values["pix_key"] and values["pix_receiver_name"]:
        options.append({"code": "PIX", "label": "PIX", "online": False})
    if values["cash_enabled"]:
        options.append({"code": "DINHEIRO", "label": "Dinheiro", "online": False})
    if values["card_on_delivery_enabled"]:
        options.append({"code": "CARTAO_ENTREGA", "label": "Cartão no atendimento/entrega", "online": False})
    if values["whatsapp_enabled"]:
        options.append({"code": "WHATSAPP", "label": "Combinar pelo WhatsApp", "online": False})
    return options


def validate_payment_method(db: Session, store: Store, method: str | None, amount) -> str | None:
    total = money(amount)
    if total <= 0:
        return None
    if not method:
        return None
    method = method.upper().strip()
    allowed = {item["code"] for item in available_payment_options(db, store)}
    if method not in allowed:
        raise HTTPException(status_code=400, detail="Forma de pagamento indisponível para esta empresa")
    return method


def _new_token(db: Session) -> str:
    for _ in range(5):
        token = secrets.token_urlsafe(18)
        if not db.query(Payment.id).filter(Payment.public_token == token).first():
            return token
    raise HTTPException(status_code=500, detail="Não foi possível gerar o protocolo do pagamento")


def create_payment(
    db: Session,
    store: Store,
    *,
    reference_type: str,
    reference_id: int,
    amount,
    method: str | None,
) -> Payment | None:
    amount = money(amount)
    method = validate_payment_method(db, store, method, amount)
    if amount <= 0 or not method:
        return None

    existing = db.query(Payment).filter(
        Payment.store_id == store.id,
        Payment.reference_type == reference_type,
        Payment.reference_id == reference_id,
    ).first()
    if existing:
        return existing

    settings = payment_settings_dict(get_settings_row(db, store.id), store.id)
    instructions = {
        "PIX": "Pague usando a chave PIX informada. A empresa confirmará o recebimento no painel.",
        "DINHEIRO": "Pagamento em dinheiro no atendimento, retirada ou entrega, conforme combinado.",
        "CARTAO_ENTREGA": "Pagamento com cartão no atendimento, retirada ou entrega, conforme combinado.",
        "WHATSAPP": "Entre em contato pelo WhatsApp da empresa para combinar o pagamento.",
    }[method]

    row = Payment(
        public_token=_new_token(db),
        store_id=store.id,
        reference_type=reference_type,
        reference_id=reference_id,
        method=method,
        provider="MANUAL",
        status="PENDENTE",
        amount=amount,
        currency="BRL",
        pix_key_type_snapshot=settings["pix_key_type"] if method == "PIX" else None,
        pix_key_snapshot=settings["pix_key"] if method == "PIX" else None,
        pix_receiver_name_snapshot=settings["pix_receiver_name"] if method == "PIX" else None,
        pix_receiver_city_snapshot=settings["pix_receiver_city"] if method == "PIX" else None,
        instructions=instructions,
    )
    db.add(row)
    db.flush()
    return row


def payment_dict(row: Payment | None) -> dict | None:
    if row is None:
        return None
    return {
        "id": row.id,
        "public_token": row.public_token,
        "reference_type": row.reference_type,
        "reference_id": row.reference_id,
        "method": row.method,
        "method_label": PAYMENT_METHOD_LABELS.get(row.method, row.method),
        "provider": row.provider,
        "status": row.status,
        "amount": row.amount,
        "currency": row.currency,
        "pix_key_type": row.pix_key_type_snapshot,
        "pix_key": row.pix_key_snapshot,
        "pix_receiver_name": row.pix_receiver_name_snapshot,
        "pix_receiver_city": row.pix_receiver_city_snapshot,
        "instructions": row.instructions,
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
        "created_at": row.created_at.isoformat(),
    }


def payment_for_reference(db: Session, store_id: int, reference_type: str, reference_id: int) -> Payment | None:
    return db.query(Payment).filter(
        Payment.store_id == store_id,
        Payment.reference_type == reference_type,
        Payment.reference_id == reference_id,
    ).first()



def cancel_reference_payment(db: Session, store_id: int, reference_type: str, reference_id: int) -> None:
    row = payment_for_reference(db, store_id, reference_type, reference_id)
    if row and row.status in {"PENDENTE", "RECUSADO"}:
        row.status = "CANCELADO"
        row.paid_at = None

def update_payment_status(db: Session, payment: Payment, new_status: str) -> Payment:
    if new_status == payment.status:
        return payment
    if new_status not in PAYMENT_TRANSITIONS.get(payment.status, set()):
        raise HTTPException(status_code=409, detail=f"Transição de pagamento {payment.status} → {new_status} não permitida")
    payment.status = new_status
    payment.paid_at = datetime.now(timezone.utc) if new_status == "PAGO" else None
    db.commit()
    db.refresh(payment)
    return payment
