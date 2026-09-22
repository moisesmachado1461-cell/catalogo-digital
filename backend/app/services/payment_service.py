from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import secrets
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.payments import Payment, PaymentSettings, StorePaymentGatewayAccount
from ..models.store import Store
from ..store_payments.mercado_pago import StoreMercadoPagoClient, StoreMercadoPagoError
from .subscription_service import feature_enabled

CENT = Decimal("0.01")
PAYMENT_METHOD_LABELS = {
    "PIX": "Pix imediato",
    "PIX_ONLINE": "Pix online",
    "DINHEIRO": "Dinheiro",
    "CARTAO_ENTREGA": "Cartão no atendimento/entrega",
    "WHATSAPP": "Combinar pelo WhatsApp",
}
PAYMENT_TRANSITIONS = {
    "PENDENTE": {"INFORMADO", "PAGO", "RECUSADO", "CANCELADO"},
    "INFORMADO": {"PAGO", "RECUSADO", "CANCELADO"},
    "RECUSADO": {"PENDENTE", "CANCELADO"},
    "PAGO": set(),
    "CANCELADO": set(),
}


def _pix_field(field_id: str, value: str) -> str:
    return f"{field_id}{len(value):02d}{value}"


def _pix_text(value: str | None, fallback: str, limit: int) -> str:
    raw = unicodedata.normalize("NFKD", value or fallback).encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch for ch in raw.upper() if ch.isalnum() or ch in " .-").strip()
    return (cleaned or fallback)[:limit]


def _pix_crc16(payload: str) -> str:
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def pix_copy_and_paste(*, key: str, amount: Decimal, receiver_name: str | None, receiver_city: str | None, reference: str) -> str:
    merchant = _pix_field("00", "BR.GOV.BCB.PIX") + _pix_field("01", key.strip())
    additional = _pix_field("05", _pix_text(reference, "CDPAGAMENTO", 25))
    payload = "".join([
        _pix_field("00", "01"),
        _pix_field("26", merchant),
        _pix_field("52", "0000"),
        _pix_field("53", "986"),
        _pix_field("54", f"{money(amount):.2f}"),
        _pix_field("58", "BR"),
        _pix_field("59", _pix_text(receiver_name, "RECEBEDOR", 25)),
        _pix_field("60", _pix_text(receiver_city, "CIDADE", 15)),
        _pix_field("62", additional),
        "6304",
    ])
    return payload + _pix_crc16(payload)


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


def get_connected_gateway_account(db: Session, store_id: int) -> StorePaymentGatewayAccount | None:
    return db.query(StorePaymentGatewayAccount).filter(
        StorePaymentGatewayAccount.store_id == store_id,
        StorePaymentGatewayAccount.provider == "MERCADO_PAGO",
        StorePaymentGatewayAccount.status == "CONNECTED",
        StorePaymentGatewayAccount.access_token_encrypted.is_not(None),
    ).first()


def available_payment_options(db: Session, store: Store) -> list[dict]:
    if not store.capabilities.get("payments", False):
        return []
    values = payment_settings_dict(get_settings_row(db, store.id), store.id)
    if not values["is_active"]:
        return []

    options: list[dict] = []
    if values["pix_enabled"] and values["pix_key"] and values["pix_receiver_name"]:
        options.append({"code": "PIX", "label": "Pix imediato", "online": False, "requires_document": False})
    if values["cash_enabled"]:
        options.append({"code": "DINHEIRO", "label": "Dinheiro", "online": False, "requires_document": False})
    if values["card_on_delivery_enabled"]:
        options.append(
            {
                "code": "CARTAO_ENTREGA",
                "label": "Cartão no atendimento/entrega",
                "online": False,
                "requires_document": False,
            }
        )
    return options


def validate_payment_method(db: Session, store: Store, method: str | None, amount) -> str | None:
    total = money(amount)
    if total <= 0 or not method:
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


def _online_pix(
    db: Session,
    payment: Payment,
    *,
    payer_email: str | None,
    payer_document: str | None,
) -> None:
    if not payer_email:
        raise HTTPException(status_code=400, detail="Informe o e-mail para pagar com Pix online")
    digits = "".join(ch for ch in (payer_document or "") if ch.isdigit())
    if len(digits) not in {11, 14}:
        raise HTTPException(status_code=400, detail="Informe CPF ou CNPJ válido para pagar com Pix online")

    account = get_connected_gateway_account(db, payment.store_id)
    if not account:
        raise HTTPException(status_code=409, detail="A loja ainda não conectou uma conta Mercado Pago")

    try:
        access_token = StoreMercadoPagoClient.ensure_access_token(db, account)
        idempotency_key = payment.provider_idempotency_key or f"storepay-{payment.public_token}"
        result = StoreMercadoPagoClient.create_pix(
            access_token=access_token,
            amount=payment.amount,
            payer_email=payer_email,
            payer_document=digits,
            external_reference=f"storepay:{payment.store_id}:{payment.reference_type}:{payment.reference_id}:{payment.id}",
            idempotency_key=idempotency_key,
        )
    except StoreMercadoPagoError as exc:
        account.last_error = str(exc)[:500]
        db.flush()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    payment.provider = "MERCADO_PAGO"
    payment.provider_idempotency_key = idempotency_key
    payment.external_id = result.order_id
    payment.provider_status = result.status_detail
    payment.status = result.status
    payment.pix_qr_code = result.qr_code
    payment.pix_qr_code_base64 = result.qr_code_base64
    payment.pix_ticket_url = result.ticket_url
    payment.instructions = "Pague pelo QR Code ou Pix Copia e Cola. A confirmação é automática."


def create_payment(
    db: Session,
    store: Store,
    *,
    reference_type: str,
    reference_id: int,
    amount,
    method: str | None,
    payer_email: str | None = None,
    payer_document: str | None = None,
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
        "PIX": "Pague usando a chave Pix informada. A empresa confirmará o recebimento no painel.",
        "PIX_ONLINE": "Aguarde a geração do QR Code Pix.",
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
        provider="MERCADO_PAGO" if method == "PIX_ONLINE" else "MANUAL",
        status="PENDENTE",
        amount=amount,
        currency="BRL",
        pix_key_type_snapshot=settings["pix_key_type"] if method == "PIX" else None,
        pix_key_snapshot=settings["pix_key"] if method == "PIX" else None,
        pix_receiver_name_snapshot=settings["pix_receiver_name"] if method == "PIX" else None,
        pix_receiver_city_snapshot=settings["pix_receiver_city"] if method == "PIX" else None,
        instructions=instructions,
    )
    if method == "PIX":
        row.pix_qr_code = pix_copy_and_paste(
            key=settings["pix_key"],
            amount=amount,
            receiver_name=settings["pix_receiver_name"],
            receiver_city=settings["pix_receiver_city"],
            reference=f"CD{reference_type}{reference_id}",
        )
    db.add(row)
    db.flush()
    if method == "PIX_ONLINE":
        _online_pix(db, row, payer_email=payer_email, payer_document=payer_document)
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
        "provider_status": row.provider_status,
        "status": row.status,
        "amount": row.amount,
        "currency": row.currency,
        "pix_key_type": row.pix_key_type_snapshot,
        "pix_key": row.pix_key_snapshot,
        "pix_receiver_name": row.pix_receiver_name_snapshot,
        "pix_receiver_city": row.pix_receiver_city_snapshot,
        "pix_qr_code": row.pix_qr_code if row.status in {"PENDENTE", "INFORMADO"} else None,
        "pix_qr_code_base64": row.pix_qr_code_base64 if row.status in {"PENDENTE", "INFORMADO"} else None,
        "pix_ticket_url": row.pix_ticket_url if row.status in {"PENDENTE", "INFORMADO"} else None,
        "pix_expires_at": row.pix_expires_at.isoformat() if row.pix_expires_at else None,
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


def sync_online_payment(db: Session, payment: Payment) -> Payment:
    if payment.provider != "MERCADO_PAGO" or not payment.external_id:
        return payment
    account = get_connected_gateway_account(db, payment.store_id)
    if not account:
        return payment
    access_token = StoreMercadoPagoClient.ensure_access_token(db, account)
    order = StoreMercadoPagoClient.get_order(access_token=access_token, order_id=str(payment.external_id))
    normalized = StoreMercadoPagoClient.order_as_payment(order)
    previous = payment.status
    payment.provider_status = normalized.get("provider_status")
    payment.status = str(normalized.get("status") or payment.status)
    if payment.status == "PAGO" and previous != "PAGO":
        payment.paid_at = datetime.now(timezone.utc)
        payment.pix_qr_code = None
        payment.pix_qr_code_base64 = None
    if payment.status in {"RECUSADO", "CANCELADO"}:
        payment.paid_at = None
    db.commit()
    db.refresh(payment)
    return payment


def cancel_reference_payment(db: Session, store_id: int, reference_type: str, reference_id: int) -> None:
    row = payment_for_reference(db, store_id, reference_type, reference_id)
    if row and row.status in {"PENDENTE", "INFORMADO", "RECUSADO"}:
        row.status = "CANCELADO"
        row.paid_at = None


def update_payment_status(db: Session, payment: Payment, new_status: str) -> Payment:
    if payment.provider != "MANUAL":
        raise HTTPException(status_code=409, detail="Pagamentos online são atualizados automaticamente pelo provedor")
    if new_status == payment.status:
        return payment
    if new_status not in PAYMENT_TRANSITIONS.get(payment.status, set()):
        raise HTTPException(status_code=409, detail=f"Transição de pagamento {payment.status} → {new_status} não permitida")
    payment.status = new_status
    payment.paid_at = datetime.now(timezone.utc) if new_status == "PAGO" else None
    db.commit()
    db.refresh(payment)
    return payment
