import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from ..config import settings
from ..models.payments import StorePaymentGatewayAccount


class StoreMercadoPagoError(RuntimeError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_error(detail: Any, status_code: int | None = None) -> str:
    parts: list[str] = []
    if isinstance(detail, dict):
        for key in ("code", "error", "message", "description"):
            value = detail.get(key)
            if isinstance(value, (str, int, float)) and str(value).strip():
                parts.append(str(value).strip()[:160])
        for key in ("errors", "details", "cause", "causes"):
            value = detail.get(key)
            items = value if isinstance(value, list) else [value] if isinstance(value, dict) else []
            for item in items[:2]:
                if not isinstance(item, dict):
                    continue
                for field in ("code", "message", "description", "field", "property"):
                    field_value = item.get(field)
                    if isinstance(field_value, (str, int, float)) and str(field_value).strip():
                        parts.append(str(field_value).strip()[:160])
    message = " · ".join(dict.fromkeys(parts)) or "Falha ao comunicar com o Mercado Pago"
    if status_code:
        message += f" (HTTP {status_code})"
    return message


def _fernet() -> Fernet:
    key = (settings.store_payment_credentials_key or "").encode("utf-8")
    if not key:
        raise StoreMercadoPagoError("Chave de proteção das credenciais das lojas não configurada")
    try:
        return Fernet(key)
    except Exception as exc:
        raise StoreMercadoPagoError("STORE_PAYMENT_CREDENTIALS_KEY inválida") from exc


def encrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise StoreMercadoPagoError("Não foi possível abrir a credencial da loja") from exc


@dataclass(frozen=True)
class StorePixResult:
    order_id: str
    payment_id: str
    status: str
    status_detail: str | None
    qr_code: str | None
    qr_code_base64: str | None
    ticket_url: str | None


class StoreMercadoPagoClient:
    api_base = "https://api.mercadopago.com"
    auth_base = "https://auth.mercadopago.com/authorization"

    @staticmethod
    def configured() -> bool:
        return settings.store_payment_marketplace_configuration_complete

    @staticmethod
    def build_authorization_url(*, state: str, code_challenge: str) -> str:
        if not StoreMercadoPagoClient.configured():
            raise StoreMercadoPagoError("Marketplace Mercado Pago ainda não configurado no servidor")
        params = {
            "client_id": settings.mercado_pago_marketplace_client_id,
            "response_type": "code",
            "platform_id": "mp",
            "state": state,
            "redirect_uri": settings.mercado_pago_marketplace_redirect_uri,
            "code_challenge": code_challenge,
            "code_method": "S256",
        }
        return f"{StoreMercadoPagoClient.auth_base}?{urlencode(params)}"

    @staticmethod
    def make_pkce() -> tuple[str, str]:
        verifier = secrets.token_urlsafe(48)[:96]
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return verifier, challenge

    @staticmethod
    def _json_request(
        method: str,
        url: str,
        *,
        payload: dict | None = None,
        access_token: str | None = None,
        idempotency_key: str | None = None,
        timeout: int = 20,
    ) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
            except Exception:
                detail = {"message": str(exc)}
            raise StoreMercadoPagoError(_safe_error(detail, exc.code)) from exc
        except (URLError, TimeoutError) as exc:
            raise StoreMercadoPagoError("Mercado Pago indisponível no momento. Tente novamente.") from exc

    @classmethod
    def exchange_authorization_code(cls, *, code: str, code_verifier: str) -> dict:
        payload = {
            "client_id": settings.mercado_pago_marketplace_client_id,
            "client_secret": settings.mercado_pago_marketplace_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.mercado_pago_marketplace_redirect_uri,
            "code_verifier": code_verifier,
            "test_token": bool(settings.store_payments_test_mode),
        }
        return cls._json_request("POST", f"{cls.api_base}/oauth/token", payload=payload)

    @classmethod
    def refresh_token(cls, refresh_token: str) -> dict:
        payload = {
            "client_id": settings.mercado_pago_marketplace_client_id,
            "client_secret": settings.mercado_pago_marketplace_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "test_token": bool(settings.store_payments_test_mode),
        }
        return cls._json_request("POST", f"{cls.api_base}/oauth/token", payload=payload)

    @classmethod
    def ensure_access_token(cls, db: Session, account: StorePaymentGatewayAccount) -> str:
        token = decrypt_secret(account.access_token_encrypted)
        if not token:
            raise StoreMercadoPagoError("Conta Mercado Pago da loja sem credencial válida")
        expires_at = account.token_expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if not expires_at or expires_at > _utcnow() + timedelta(days=7):
            return token
        refresh = decrypt_secret(account.refresh_token_encrypted)
        if not refresh:
            account.status = "RECONNECT_REQUIRED"
            db.flush()
            raise StoreMercadoPagoError("A loja precisa reconectar a conta Mercado Pago")
        data = cls.refresh_token(refresh)
        new_token = str(data.get("access_token") or "")
        if not new_token:
            raise StoreMercadoPagoError("Mercado Pago não retornou um novo Access Token")
        account.access_token_encrypted = encrypt_secret(new_token)
        if data.get("refresh_token"):
            account.refresh_token_encrypted = encrypt_secret(str(data["refresh_token"]))
        expires_in = int(data.get("expires_in") or 0)
        account.token_expires_at = _utcnow() + timedelta(seconds=expires_in) if expires_in else None
        account.status = "CONNECTED"
        account.last_error = None
        account.updated_at = _utcnow()
        db.flush()
        return new_token

    @staticmethod
    def order_as_payment(order: dict[str, Any]) -> dict[str, Any]:
        transactions = order.get("transactions") or {}
        payments = transactions.get("payments") or []
        tx = payments[0] if payments else {}
        method = tx.get("payment_method") or {}
        order_status = str(order.get("status") or tx.get("status") or "created").lower()
        detail = str(order.get("status_detail") or tx.get("status_detail") or "")
        if order_status == "processed" and detail in {"accredited", "processed", ""}:
            normalized = "PAGO"
        elif order_status in {"failed"}:
            normalized = "RECUSADO"
        elif order_status in {"canceled", "cancelled", "expired"}:
            normalized = "CANCELADO"
        else:
            normalized = "PENDENTE"
        return {
            "order_id": order.get("id"),
            "payment_id": tx.get("id") or order.get("id"),
            "status": normalized,
            "provider_status": f"{order_status}:{detail}" if detail else order_status,
            "qr_code": method.get("qr_code"),
            "qr_code_base64": method.get("qr_code_base64"),
            "ticket_url": method.get("ticket_url"),
            "external_reference": order.get("external_reference"),
        }

    @classmethod
    def create_pix(
        cls,
        *,
        access_token: str,
        amount: Decimal,
        payer_email: str,
        payer_document: str,
        external_reference: str,
        idempotency_key: str,
    ) -> StorePixResult:
        amount_text = f"{Decimal(amount).quantize(Decimal('0.01')):.2f}"
        payload = {
            "type": "online",
            "processing_mode": "automatic",
            "external_reference": external_reference[:64],
            "total_amount": amount_text,
            "payer": {
                "email": payer_email,
                "identification": {
                    "type": "CNPJ" if len("".join(ch for ch in payer_document if ch.isdigit())) == 14 else "CPF",
                    "number": "".join(ch for ch in payer_document if ch.isdigit()),
                },
            },
            "transactions": {
                "payments": [
                    {
                        "amount": amount_text,
                        "payment_method": {"id": "pix", "type": "bank_transfer"},
                    }
                ]
            },
        }
        order = cls._json_request(
            "POST",
            f"{cls.api_base}/v1/orders",
            payload=payload,
            access_token=access_token,
            idempotency_key=idempotency_key,
        )
        normalized = cls.order_as_payment(order)
        if not normalized["order_id"]:
            raise StoreMercadoPagoError("Mercado Pago não retornou o identificador da cobrança")
        return StorePixResult(
            order_id=str(normalized["order_id"]),
            payment_id=str(normalized["payment_id"]),
            status=str(normalized["status"]),
            status_detail=normalized.get("provider_status"),
            qr_code=normalized.get("qr_code"),
            qr_code_base64=normalized.get("qr_code_base64"),
            ticket_url=normalized.get("ticket_url"),
        )

    @classmethod
    def get_order(cls, *, access_token: str, order_id: str) -> dict:
        return cls._json_request("GET", f"{cls.api_base}/v1/orders/{order_id}", access_token=access_token)

    @staticmethod
    def validate_webhook_signature(
        *,
        x_signature: str | None,
        x_request_id: str | None,
        data_id: str | None,
        secret: str | None,
    ) -> bool:
        if not (x_signature and data_id and secret):
            return False
        values: dict[str, str] = {}
        for item in x_signature.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                values[key.strip()] = value.strip()
        ts = values.get("ts")
        received = values.get("v1")
        if not (ts and received):
            return False
        manifest = f"id:{data_id};"
        if x_request_id:
            manifest += f"request-id:{x_request_id};"
        manifest += f"ts:{ts};"
        calculated = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calculated, received)
