# Fase 24.9.4 — OAuth Marketplace: APP ID x Client ID

## Causa

O Mercado Pago usa dois identificadores diferentes no mesmo fluxo OAuth:

- **APP ID** (número da aplicação) na URL `https://auth.mercadopago.com/authorization`;
- **Client ID + Client Secret** na troca do `authorization_code` em `POST /oauth/token`.

Usar uma única variável para as duas etapas fazia uma delas falhar: se fosse usado o APP ID na troca, surgia `invalid_client`; se fosse usado o Client ID na autorização, a aplicação podia ser recusada antes do consentimento.

## Variáveis

```text
MERCADO_PAGO_MARKETPLACE_APP_ID=<ID numérico da aplicação Marketplace>
MERCADO_PAGO_MARKETPLACE_CLIENT_ID=<Client ID das credenciais da mesma aplicação>
MERCADO_PAGO_MARKETPLACE_CLIENT_SECRET=<Client Secret da mesma aplicação>
MERCADO_PAGO_MARKETPLACE_REDIRECT_URI=https://catalogo-digital-api.onrender.com/api/payment-gateways/mercado-pago/callback
```

Não misture dados da aplicação `Catálogo Digital SaaS` com a aplicação `Catálogo Digital Marketplace`.

Não há migration nesta fase.
