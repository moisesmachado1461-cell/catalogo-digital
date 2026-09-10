from dataclasses import dataclass

from .base import BillingGateway


@dataclass(frozen=True)
class ProviderDescriptor:
    code: str
    display_name: str
    automatic: bool
    supports: tuple[str, ...]


# Provedores previstos pela arquitetura. A disponibilidade real só passa a True
# quando um adaptador funcional e suas credenciais forem configurados.
PROVIDER_CATALOG: dict[str, ProviderDescriptor] = {
    "MERCADO_PAGO": ProviderDescriptor(
        code="MERCADO_PAGO",
        display_name="Mercado Pago",
        automatic=True,
        supports=("RECURRENCE",),
    ),
    "PIX_AUTOMATICO": ProviderDescriptor(
        code="PIX_AUTOMATICO",
        display_name="Pix Automático",
        automatic=True,
        supports=("PIX_AUTOMATICO", "RECURRENCE"),
    ),
    "PICPAY": ProviderDescriptor(
        code="PICPAY",
        display_name="PicPay",
        automatic=True,
        supports=("RECURRENCE",),
    ),
    "MANUAL": ProviderDescriptor(
        code="MANUAL",
        display_name="Controle manual",
        automatic=False,
        supports=("MANUAL",),
    ),
}

_GATEWAYS: dict[str, BillingGateway] = {}


def normalize_provider(value: str) -> str:
    return value.strip().upper().replace("-", "_").replace(" ", "_")


def register_gateway(gateway: BillingGateway) -> None:
    code = normalize_provider(gateway.code)
    if code not in PROVIDER_CATALOG:
        raise ValueError(f"Gateway não cadastrado no catálogo: {code}")
    _GATEWAYS[code] = gateway


def get_gateway(provider: str) -> BillingGateway | None:
    return _GATEWAYS.get(normalize_provider(provider))


def provider_statuses() -> list[dict]:
    rows: list[dict] = []
    for code, descriptor in PROVIDER_CATALOG.items():
        gateway = _GATEWAYS.get(code)
        configured = bool(gateway and gateway.is_configured())
        rows.append(
            {
                "code": code,
                "display_name": descriptor.display_name,
                "automatic": descriptor.automatic,
                "supports": list(descriptor.supports),
                "adapter_registered": gateway is not None,
                "configured": configured,
                "available_for_checkout": configured,
            }
        )
    return rows
