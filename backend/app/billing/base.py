from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BillingCheckoutRequest:
    store_id: int
    plan_id: int
    billing_cycle: str
    amount: Decimal
    currency: str
    payer_email: str | None
    success_url: str | None
    cancel_url: str | None


@dataclass(frozen=True)
class BillingCheckoutResult:
    provider: str
    external_subscription_id: str | None
    external_customer_id: str | None
    external_invoice_id: str | None
    checkout_url: str
    raw_status: str | None = None


@dataclass(frozen=True)
class GatewaySubscriptionState:
    provider: str
    external_subscription_id: str
    status: str
    next_billing_at: Any | None = None
    current_period_end: Any | None = None


class BillingGateway(ABC):
    """Contrato único para gateways de cobrança recorrente do SaaS."""

    code: str
    display_name: str

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_subscription_checkout(self, request: BillingCheckoutRequest) -> BillingCheckoutResult:
        raise NotImplementedError

    @abstractmethod
    def cancel_subscription(self, external_subscription_id: str, *, at_period_end: bool = True) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch_subscription(self, external_subscription_id: str) -> GatewaySubscriptionState:
        raise NotImplementedError
