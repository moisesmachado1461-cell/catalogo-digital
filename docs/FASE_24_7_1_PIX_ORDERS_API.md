# Fase 24.7.1 — Pix Mercado Pago via Orders API

Correção da integração Pix da cobrança SaaS para o fluxo atual do Checkout Transparente do Mercado Pago.

## Mudanças
- criação de Pix via `POST /v1/orders`;
- consulta de Pix via `GET /v1/orders/{id}`;
- leitura de QR Code/Copia e Cola pela transação da order;
- normalização dos status de order para o estado interno das faturas;
- suporte a webhook do tópico `Order (Mercado Pago)`;
- compatibilidade temporária com webhook `payment` legado;
- cenário oficial de teste Pix com e-mail `test_user_br@testuser.com`;
- sem nova migration de banco.

## Mercado Pago
No painel da aplicação, o webhook deve usar o evento **Order (Mercado Pago)** para o fluxo Checkout Transparente via Orders API.
