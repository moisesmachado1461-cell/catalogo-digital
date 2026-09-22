"""Cobrança das assinaturas do próprio SaaS Catálogo Digital."""

from .mercado_pago import MercadoPagoGateway
from .registry import register_gateway

# Registro central do primeiro gateway real. A disponibilidade só fica ativa
# quando as credenciais seguras estão configuradas no backend/Render.
register_gateway(MercadoPagoGateway())
