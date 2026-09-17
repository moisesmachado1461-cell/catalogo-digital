# Fase 24.4.1 — Integração da correção de restore drill

Esta correção consolida na base 24.4 a melhoria que existia na Fase 24.3.1.

## Mudança

O workflow `.github/workflows/restore-drill.yml` passa a subir um PostgreSQL 18 temporário dentro do GitHub Actions. O banco é usado exclusivamente para aplicar migrations, restaurar o backup e validar a recuperação, sendo descartado ao final da execução.

## Secrets necessários

- `BACKUP_DATABASE_URL`
- `BACKUP_ENCRYPTION_KEY`

O secret `RESTORE_TEST_DATABASE_URL` não é mais necessário.

## Segurança

O banco de produção continua sendo somente a origem lógica do backup. A restauração ocorre no PostgreSQL temporário do workflow, nunca sobre o banco de produção.

## Pendência operacional

Executar manualmente **GitHub → Actions → Restore drill do PostgreSQL → Run workflow** e confirmar sucesso antes do lançamento.
