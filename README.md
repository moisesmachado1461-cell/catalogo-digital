# Catálogo Digital — Fase 24.9.5

Hotfix do OAuth Mercado Pago Marketplace.

## Correção

A documentação específica de Split Payments 1:1 define o `client_id` do `/oauth/token` como o próprio **APP ID** obtido nos detalhes da aplicação. A fase 24.9.4 separou APP ID e Client ID, mas manteve um Client ID separado na troca do token. Isso podia continuar produzindo `invalid_client`.

A 24.9.5:

- usa `MERCADO_PAGO_MARKETPLACE_APP_ID` na autorização e na troca/renovação OAuth;
- mantém o segredo da aplicação em `MERCADO_PAGO_MARKETPLACE_CLIENT_SECRET`;
- envia o token request como `application/x-www-form-urlencoded`;
- preserva PKCE S256;
- não cria migration.
