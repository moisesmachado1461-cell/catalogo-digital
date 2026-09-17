# Fase 24.9.0 — Pagamentos online dos clientes das lojas

## Objetivo

Permitir que cada estabelecimento receba Pix online diretamente em sua própria conta Mercado Pago, sem misturar esse dinheiro com a cobrança da assinatura do Catálogo Digital.

## Arquitetura

- O Admin conecta a própria conta Mercado Pago pelo fluxo OAuth Authorization Code com PKCE.
- O backend guarda Access Token e refresh token criptografados com Fernet.
- O frontend nunca recebe credenciais do vendedor.
- O checkout cria a cobrança usando o Access Token da loja conectada.
- O valor é processado na conta Mercado Pago daquela loja.
- O webhook da aplicação Marketplace atualiza o pagamento automaticamente.
- Consulta por token público funciona como fallback de sincronização.

## Formas de pagamento

Continuam disponíveis as opções manuais já existentes:

- Pix manual;
- dinheiro;
- cartão no atendimento/entrega;
- combinar via WhatsApp.

Quando a loja possui plano com `online_payments` e conta Mercado Pago conectada, aparece também:

- **Pix online · confirmação automática**.

## Segurança

- OAuth usa `state` aleatório e PKCE S256.
- O `code_verifier` temporário fica criptografado no banco.
- Tokens permanentes/refresh ficam criptografados.
- `STORE_PAYMENT_CREDENTIALS_KEY` nunca deve ir para Git/GitHub.
- Webhooks usam validação de assinatura.
- Pagamentos online não podem ser marcados manualmente como pagos pelo Admin.

## Variáveis de ambiente

```text
MERCADO_PAGO_MARKETPLACE_CLIENT_ID
MERCADO_PAGO_MARKETPLACE_CLIENT_SECRET
MERCADO_PAGO_MARKETPLACE_REDIRECT_URI
MERCADO_PAGO_MARKETPLACE_WEBHOOK_SECRET
STORE_PAYMENT_CREDENTIALS_KEY
STORE_PAYMENTS_TEST_MODE=false
FRONTEND_PUBLIC_URL=https://catalogo-digital-v3zs.onrender.com
```

Redirect URL de produção:

```text
https://catalogo-digital-api.onrender.com/api/payment-gateways/mercado-pago/callback
```

Webhook de produção:

```text
https://catalogo-digital-api.onrender.com/api/payment-gateways/webhooks/mercado-pago
```

## Banco de dados

Migration: `020_store_marketplace_payments`.

Ela adiciona:

- dados de QR/status do provedor em `payments`;
- `store_payment_gateway_accounts`;
- `store_payment_oauth_states`.

## Fluxo do cliente

1. Cliente finaliza pedido/agendamento/reserva/locação.
2. Seleciona Pix online.
3. Informa e-mail e CPF/CNPJ.
4. Recebe QR Code e Pix Copia e Cola.
5. Paga no banco.
6. Mercado Pago notifica o Catálogo Digital.
7. Pagamento muda para `PAGO` automaticamente.

## Regra financeira

A mensalidade SaaS e as vendas das lojas são fluxos financeiros independentes. O Catálogo Digital não usa a própria conta Mercado Pago para receber as vendas das lojas.
