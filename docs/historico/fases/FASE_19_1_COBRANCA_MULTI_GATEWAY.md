# Fase 19.1 — Fundação de cobrança automática multi-gateway

Esta fase separa formalmente duas áreas financeiras do Catálogo Digital:

1. `payments`: pagamento que o cliente final faz para uma loja.
2. `billing`: cobrança da assinatura que a loja paga para usar o SaaS Catálogo Digital.

## Objetivo

Preparar a cobrança recorrente sem prender a plataforma a um único provedor.

Catálogo interno de provedores:

- `MERCADO_PAGO`
- `PIX_AUTOMATICO`
- `PICPAY`
- `MANUAL`

Um meio automático só é marcado como disponível quando existir um adaptador real configurado. Nenhum checkout falso é criado nesta fase.

## Banco

A migration `011_subscription_billing` adiciona:

- metadados de renovação automática em `subscriptions`;
- `billing_gateway_prices`: mapeamento plano interno → preço/ID do gateway;
- `subscription_invoices`: histórico financeiro da assinatura SaaS;
- `billing_webhook_events`: idempotência e auditoria mínima de webhooks sem guardar o corpo bruto.

## API nova

Admin da loja:

- `GET /api/admin/billing/providers`
- `GET /api/admin/billing/overview`

Super Admin:

- `GET /api/super-admin/billing/providers`
- `GET /api/super-admin/billing/gateway-prices`
- `POST /api/super-admin/billing/gateway-prices`
- `PATCH /api/super-admin/billing/gateway-prices/{gateway_price_id}`

## Segurança

- `store_id` continua vindo do usuário autenticado no backend.
- segredos de gateways não são armazenados nessas tabelas;
- webhooks futuros usarão verificação de assinatura + idempotência;
- o payload bruto dos webhooks não é persistido nessa camada.

## Próxima fase

Fase 19.2: primeiro adaptador real de cobrança recorrente, começando pelo Mercado Pago e mantendo o contrato multi-gateway.
