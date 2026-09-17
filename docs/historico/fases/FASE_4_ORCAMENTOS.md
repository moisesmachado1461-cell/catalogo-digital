# Fase 4 — Orçamentos

Esta fase adiciona o fluxo de solicitação de orçamento para empresas como eletricistas, encanadores, oficinas, assistência técnica, pintores e prestadores de serviço.

## Banco

Migration `004_quotes`:
- `quote_requests`
- `quote_attachments`

## Fluxo público

1. Cliente acessa uma loja com capability `quotes`.
2. Cliente informa contato, tipo de serviço, título, descrição e endereço opcional.
3. A API cria a solicitação com status `RECEBIDO`.
4. A API retorna um `public_token` não sequencial para acompanhamento público.
5. O cliente pode consultar o andamento usando esse token.

## Fluxo administrativo

- Listar solicitações da própria loja.
- Abrir uma solicitação específica.
- Alterar status.
- Informar valor estimado, mensagem e validade da proposta.

## Status

`RECEBIDO → EM_ANALISE → ORCAMENTO_ENVIADO → APROVADO → CONCLUIDO`

Também há `RECUSADO` e `CANCELADO` conforme as transições permitidas.

## Multi-tenant

Todas as consultas administrativas usam o `store_id` derivado do JWT do administrador. IDs de outra loja resultam em `404`.

## Anexos

Nesta fase a API registra metadados e URLs de anexos. Upload binário/storage externo será implementado na fase específica de arquivos e storage.
