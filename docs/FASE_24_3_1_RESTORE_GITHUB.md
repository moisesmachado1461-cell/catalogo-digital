# Fase 24.3.1 — Restore drill no GitHub Actions

O plano gratuito do Render permite apenas um PostgreSQL free ativo. Para não exigir upgrade ou segundo provedor, o restore drill agora sobe um PostgreSQL 18 temporário dentro do próprio GitHub Actions.

Secrets necessários:
- BACKUP_DATABASE_URL
- BACKUP_ENCRYPTION_KEY

O secret RESTORE_TEST_DATABASE_URL não é mais necessário.

O PostgreSQL temporário existe apenas durante o workflow, recebe as migrations e o restore, é validado e depois descartado automaticamente.
