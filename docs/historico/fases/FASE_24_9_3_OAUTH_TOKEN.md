# Fase 24.9.3 — correção da troca OAuth do Marketplace

Objetivo: tornar a etapa final do OAuth Mercado Pago previsível e diagnosticável sem expor segredos.

## Alterações

- `test_token` é enviado como string `"true"` ou `"false"`, conforme exemplos oficiais da API OAuth.
- PKCE continua usando `code_challenge_method=S256` na autorização e `code_verifier` na troca de token.
- erros retornados por `/oauth/token` são reduzidos a mensagens sanitizadas.
- o callback devolve ao Admin somente o motivo seguro da falha.
- o Admin apresenta mensagens específicas para `invalid_client`, `invalid_grant`, `unauthorized_client` e `invalid_request`.

Não há migration nesta fase.
