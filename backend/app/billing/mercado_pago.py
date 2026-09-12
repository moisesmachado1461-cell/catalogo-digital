import hashlib
import hmac
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import settings
from .base import BillingCheckoutRequest, BillingCheckoutResult, BillingGateway, GatewaySubscriptionState


class MercadoPagoError(RuntimeError):
    pass


@dataclass(frozen=True)
class PixPaymentResult:
    payment_id: str
    order_id: str | None
    status: str
    status_detail: str | None
    qr_code: str | None
    qr_code_base64: str | None
    ticket_url: str | None
    raw: dict[str, Any]


class MercadoPagoGateway(BillingGateway):
    code = "MERCADO_PAGO"
    display_name = "Mercado Pago"
    api_base = "https://api.mercadopago.com"

    def is_configured(self) -> bool:
        # Exigimos token + segredo do webhook para que a ativação automática seja segura.
        return bool(settings.mercado_pago_access_token and settings.mercado_pago_webhook_secret)

    @property
    def pix_ready(self) -> bool:
        return self.is_configured()

    def _request(self, method: str, path: str, *, payload: dict | None = None, idempotency_key: str | None = None) -> dict:
        if not settings.mercado_pago_access_token:
            raise MercadoPagoError("Mercado Pago ainda não está configurado no servidor")
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Authorization": f"Bearer {settings.mercado_pago_access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        request = Request(f"{self.api_base}{path}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
            except Exception:
                detail = {"message": str(exc)}
            message = detail.get("message") or detail.get("error")
            if not message:
                cause = detail.get("cause") or detail.get("causes") or detail.get("details") or []
                if isinstance(cause, list) and cause:
                    first = cause[0] if isinstance(cause[0], dict) else {}
                    message = first.get("description") or first.get("message") or first.get("code")
            message = message or "Falha ao comunicar com o Mercado Pago"
            raise MercadoPagoError(str(message)) from exc
        except (URLError, TimeoutError) as exc:
            raise MercadoPagoError("Mercado Pago indisponível no momento. Tente novamente.") from exc

    @staticmethod
    def order_as_payment(order: dict[str, Any]) -> dict[str, Any]:
        transactions = order.get("transactions") or {}
        payments = transactions.get("payments") or []
        tx = payments[0] if payments else {}
        payment_method = tx.get("payment_method") or {}
        order_status = str(order.get("status") or tx.get("status") or "created").lower()
        order_detail = str(order.get("status_detail") or tx.get("status_detail") or "")

        if order_status == "processed" and order_detail in {"accredited", "processed", ""}:
            normalized_status = "approved"
        elif order_status in {"failed"}:
            normalized_status = "rejected"
        elif order_status in {"canceled", "cancelled", "expired"}:
            normalized_status = "cancelled"
        elif order_status == "refunded":
            normalized_status = "refunded"
        elif order_status == "charged_back":
            normalized_status = "charged_back"
        elif order_status == "processing":
            normalized_status = "in_process"
        else:
            normalized_status = "pending"

        return {
            "id": tx.get("id") or order.get("id"),
            "status": normalized_status,
            "status_detail": order_detail or tx.get("status_detail"),
            "transaction_amount": order.get("total_amount") or tx.get("amount") or "0",
            "currency_id": "BRL",
            "payment_method_id": "pix",
            "external_reference": order.get("external_reference"),
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": payment_method.get("qr_code"),
                    "qr_code_base64": payment_method.get("qr_code_base64"),
                    "ticket_url": payment_method.get("ticket_url"),
                }
            },
            "_order_id": order.get("id"),
            "_order_status": order_status,
        }

    def create_pix_payment(
        self,
        *,
        amount: Decimal,
        description: str,
        payer_email: str,
        document_type: str,
        document_number: str,
        external_reference: str,
        idempotency_key: str,
        notification_url: str | None,
    ) -> PixPaymentResult:
        # Desde 2025/2026, o fluxo recomendado do Checkout Transparente para Pix
        # usa Orders API. O endpoint legado /v1/payments pode retornar internal_error
        # em testes com as credenciais atuais.
        amount_text = f"{Decimal(amount).quantize(Decimal('0.01')):.2f}"
        payer: dict[str, Any] = {"email": payer_email}
        # Cenário de teste oficial do Mercado Pago para Pix via Orders. Para o
        # pagador de teste usamos exatamente os campos do cenário documentado.
        if payer_email.strip().lower() == "test_user_br@testuser.com":
            payer["first_name"] = "APRO"
        else:
            payer["identification"] = {"type": document_type, "number": document_number}

        payload: dict[str, Any] = {
            "type": "online",
            "processing_mode": "automatic",
            "external_reference": external_reference[:64],
            "total_amount": amount_text,
            "payer": payer,
            "transactions": {
                "payments": [
                    {
                        "amount": amount_text,
                        "payment_method": {"id": "pix", "type": "bank_transfer"},
                    }
                ]
            },
        }
        # A URL de webhook é configurada no painel da aplicação. Não enviamos
        # notification_url no body da Orders API para evitar parâmetros legados.
        data = self._request("POST", "/v1/orders", payload=payload, idempotency_key=idempotency_key)
        normalized = self.order_as_payment(data)
        transaction = ((normalized.get("point_of_interaction") or {}).get("transaction_data") or {})
        order_id = data.get("id")
        payment_id = normalized.get("id")
        if order_id is None:
            raise MercadoPagoError("Mercado Pago não retornou o identificador da order")
        if payment_id is None:
            payment_id = order_id
        return PixPaymentResult(
            payment_id=str(payment_id),
            order_id=str(order_id),
            status=str(normalized.get("status") or "pending"),
            status_detail=normalized.get("status_detail"),
            qr_code=transaction.get("qr_code"),
            qr_code_base64=transaction.get("qr_code_base64"),
            ticket_url=transaction.get("ticket_url"),
            raw=normalized,
        )

    def get_order(self, order_id: str) -> dict:
        return self._request("GET", f"/v1/orders/{order_id}")

    def getorder_as_payment(self, order_id: str) -> dict:
        return self.order_as_payment(self.get_order(order_id))

    def get_payment(self, payment_id: str) -> dict:
        return self._request("GET", f"/v1/payments/{payment_id}")

    @staticmethod
    def validate_webhook_signature(*, x_signature: str | None, x_request_id: str | None, data_id: str | None, secret: str | None) -> bool:
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
        parts = [f"id:{data_id};"]
        if x_request_id:
            parts.append(f"request-id:{x_request_id};")
        parts.append(f"ts:{ts};")
        manifest = "".join(parts)
        calculated = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calculated, received)

    # A arquitetura continua pronta para recorrência, mas a Fase 24.7 habilita Pix imediato.
    def create_subscription_checkout(self, request: BillingCheckoutRequest) -> BillingCheckoutResult:
        raise NotImplementedError("Recorrência automática ainda não habilitada; use Pix imediato")

    def cancel_subscription(self, external_subscription_id: str, *, at_period_end: bool = True) -> None:
        raise NotImplementedError("Assinatura recorrente Mercado Pago ainda não habilitada")

    def fetch_subscription(self, external_subscription_id: str) -> GatewaySubscriptionState:
        raise NotImplementedError("Assinatura recorrente Mercado Pago ainda não habilitada")
