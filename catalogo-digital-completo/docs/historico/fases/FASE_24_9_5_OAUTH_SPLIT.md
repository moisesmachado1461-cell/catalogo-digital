# Fase 24.9.5 — OAuth Split/Marketplace

Correção do `invalid_client` persistente no callback OAuth.

A documentação específica do Mercado Pago para Split Payments 1:1 define que:

- a autorização usa o APP ID da aplicação;
- o campo `client_id` enviado a `/oauth/token` também recebe o valor do APP ID;
- o segredo é a SECRET_KEY/Client Secret da mesma aplicação;
- a troca de token é enviada como `application/x-www-form-urlencoded`.

O projeto passa a seguir esse fluxo no authorization code e na renovação do token.
Nenhuma migration é necessária.
