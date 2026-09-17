# Fase 18.4 — Limpeza do teste do Sentry

O teste controlado do Sentry já foi concluído.

Este patch remove a rota temporária:

POST /api/super-admin/monitoring/sentry-test

O Sentry continua configurado normalmente por SENTRY_DSN e
SENTRY_TRACES_SAMPLE_RATE. Nenhuma migration de banco é necessária.

Após publicar:
1. Confirme /api/health.
2. A rota temporária não deve mais aparecer no Swagger.
3. O monitoramento real do Sentry permanece ativo para erros da aplicação.
