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
            message = detail.get("message") or detail.get("error") or "Falha ao comunicar com o Mercado Pago"
            raise MercadoPagoError(str(message)) from exc
        except (URLError, TimeoutError) as exc:
            raise MercadoPagoError("Mercado Pago indisponível no momento. Tente novamente.") from exc

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
        payload: dict[str, Any] = {
            "transaction_amount": float(Decimal(amount).quantize(Decimal("0.01"))),
            "description": description[:150],
            "payment_method_id": "pix",
            "external_reference": external_reference[:64],
            "payer": {
                "email": payer_email,
                "identification": {"type": document_type, "number": document_number},
            },
        }
        if notification_url:
            payload["notification_url"] = notification_url
        data = self._request("POST", "/v1/payments", payload=payload, idempotency_key=idempotency_key)
        transaction = ((data.get("point_of_interaction") or {}).get("transaction_data") or {})
        payment_id = data.get("id")
        if payment_id is None:
            raise MercadoPagoError("Mercado Pago não retornou o identificador do pagamento")
        return PixPaymentResult(
            payment_id=str(payment_id),
            status=str(data.get("status") or "pending"),
            status_detail=data.get("status_detail"),
            qr_code=transaction.get("qr_code"),
            qr_code_base64=transaction.get("qr_code_base64"),
            ticket_url=transaction.get("ticket_url"),
            raw=data,
        )

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
