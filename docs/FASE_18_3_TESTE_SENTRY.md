# Fase 18.3 — Teste controlado do Sentry

Este patch adiciona uma rota temporária protegida por autenticação de Super Admin:

`POST /api/super-admin/monitoring/sentry-test`

A rota não gera erro 500, não altera banco e não mexe em pedidos, agendamentos ou lojas. Ela apenas envia ao Sentry a mensagem:

`Catálogo Digital - teste de monitoramento`

Depois de confirmar que o evento chegou ao Sentry, esta rota pode ser removida em uma atualização posterior.
