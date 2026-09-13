import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_store_id
from ..models.payments import Payment, PaymentSettings, StorePaymentGatewayAccount, StorePaymentOAuthState
from ..services.payment_service import sync_online_payment
from ..services.subscription_service import require_feature
from ..store_payments.mercado_pago import (
    StoreMercadoPagoClient,
    StoreMercadoPagoError,
    decrypt_secret,
    encrypt_secret,
)

admin_router = APIRouter(prefix="/api/admin/payment-gateways", tags=["store-payment-gateways-admin"])
public_router = APIRouter(prefix="/api/payment-gateways", tags=["store-payment-gateways-public"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _account(db: Session, store_id: int) -> StorePaymentGatewayAccount | None:
    return db.query(StorePaymentGatewayAccount).filter(
        StorePaymentGatewayAccount.store_id == store_id,
        StorePaymentGatewayAccount.provider == "MERCADO_PAGO",
    ).first()


def _status_payload(db: Session, store_id: int) -> dict:
    account = _account(db, store_id)
    configured = StoreMercadoPagoClient.configured()
    connected = bool(account and account.status == "CONNECTED" and account.access_token_encrypted)
    return {
        "provider": "MERCADO_PAGO",
        "configured": configured,
        "connected": connected,
        "status": account.status if account else "NOT_CONNECTED",
        "external_user_id": account.external_user_id if account else None,
        "connected_at": account.connected_at.isoformat() if account else None,
        "token_expires_at": account.token_expires_at.isoformat() if account and account.token_expires_at else None,
        "test_mode": bool(settings.store_payments_test_mode),
    }


@admin_router.get("/mercado-pago/status")
def mercado_pago_status(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    return _status_payload(db, store_id)


@admin_router.post("/mercado-pago/connect")
def mercado_pago_connect(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    require_feature(db, store_id, "online_payments")
    if not StoreMercadoPagoClient.configured():
        raise HTTPException(status_code=503, detail="Marketplace Mercado Pago ainda não foi configurado no servidor")

    raw_state = secrets.token_urlsafe(32)
    state_digest = hashlib.sha256(raw_state.encode("utf-8")).hexdigest()
    verifier, challenge = StoreMercadoPagoClient.make_pkce()
    now = _utcnow()

    db.query(StorePaymentOAuthState).filter(
        StorePaymentOAuthState.store_id == store_id,
        StorePaymentOAuthState.provider == "MERCADO_PAGO",
        StorePaymentOAuthState.consumed_at.is_(None),
    ).delete(synchronize_session=False)
    db.add(
        StorePaymentOAuthState(
            store_id=store_id,
            provider="MERCADO_PAGO",
            state_digest=state_digest,
            code_verifier_encrypted=encrypt_secret(verifier),
            expires_at=now + timedelta(minutes=10),
        )
    )
    db.commit()
    return {
        "authorization_url": StoreMercadoPagoClient.build_authorization_url(
            state=raw_state,
            code_challenge=challenge,
        )
    }


@admin_router.delete("/mercado-pago")
def mercado_pago_disconnect(store_id: int = Depends(get_current_store_id), db: Session = Depends(get_db)):
    account = _account(db, store_id)
    if account:
        db.delete(account)
    settings_row = db.query(PaymentSettings).filter(PaymentSettings.store_id == store_id).first()
    if settings_row:
        settings_row.online_gateway = "NONE"
    db.commit()
    return {"status": "disconnected"}


@public_router.get("/mercado-pago/callback")
def mercado_pago_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    frontend = settings.public_frontend_base_url or "/"
    target = f"{frontend}/admin.html"
    if error or not code or not state:
        return RedirectResponse(f"{target}?payment_gateway=error&reason=authorization")

    digest = hashlib.sha256(state.encode("utf-8")).hexdigest()
    row = db.query(StorePaymentOAuthState).filter(
        StorePaymentOAuthState.state_digest == digest,
        StorePaymentOAuthState.provider == "MERCADO_PAGO",
        StorePaymentOAuthState.consumed_at.is_(None),
    ).first()
    now = _utcnow()
    if not row:
        return RedirectResponse(f"{target}?payment_gateway=error&reason=state")
    expires_at = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        row.consumed_at = now
        db.commit()
        return RedirectResponse(f"{target}?payment_gateway=error&reason=expired")

    try:
        verifier = decrypt_secret(row.code_verifier_encrypted)
        token_data = StoreMercadoPagoClient.exchange_authorization_code(code=code, code_verifier=verifier or "")
    except StoreMercadoPagoError:
        row.consumed_at = now
        db.commit()
        return RedirectResponse(f"{target}?payment_gateway=error&reason=token")

    access_token = str(token_data.get("access_token") or "")
    if not access_token:
        row.consumed_at = now
        db.commit()
        return RedirectResponse(f"{target}?payment_gateway=error&reason=token")

    account = _account(db, row.store_id)
    if not account:
        account = StorePaymentGatewayAccount(store_id=row.store_id, provider="MERCADO_PAGO")
        db.add(account)
    account.external_user_id = str(token_data.get("user_id") or "") or None
    account.access_token_encrypted = encrypt_secret(access_token)
    account.refresh_token_encrypted = encrypt_secret(str(token_data.get("refresh_token") or ""))
    expires_in = int(token_data.get("expires_in") or 0)
    account.token_expires_at = now + timedelta(seconds=expires_in) if expires_in else None
    account.scope = str(token_data.get("scope") or "") or None
    account.status = "CONNECTED"
    account.last_error = None
    account.connected_at = now
    account.updated_at = now
    row.consumed_at = now

    settings_row = db.query(PaymentSettings).filter(PaymentSettings.store_id == row.store_id).first()
    if not settings_row:
        settings_row = PaymentSettings(store_id=row.store_id)
        db.add(settings_row)
    settings_row.online_gateway = "MERCADO_PAGO"
    settings_row.is_active = True
    db.commit()
    return RedirectResponse(f"{target}?payment_gateway=connected")


@public_router.post("/webhooks/mercado-pago")
async def mercado_pago_store_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    body = await request.json()
    data = body.get("data") or {}
    resource_id = str(data.get("id") or body.get("id") or "")
    if not resource_id:
        return {"ok": True, "ignored": "missing_id"}

    if not StoreMercadoPagoClient.validate_webhook_signature(
        x_signature=x_signature,
        x_request_id=x_request_id,
        data_id=resource_id,
        secret=settings.mercado_pago_marketplace_webhook_secret,
    ):
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida")

    payment = db.query(Payment).filter(
        Payment.provider == "MERCADO_PAGO",
        Payment.external_id == resource_id,
    ).first()
    if not payment:
        return {"ok": True, "ignored": "payment_not_found"}

    try:
        sync_online_payment(db, payment)
    except StoreMercadoPagoError as exc:
        return {"ok": False, "detail": str(exc)[:240]}
    return {"ok": True, "payment_id": payment.id, "status": payment.status}
