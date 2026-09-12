# Fase 24.3 — Backup automático, restore drill e recuperação de desastre

## Objetivo

Reduzir o risco de perda de dados e provar que um backup pode ser lido e restaurado em um banco separado.

## O que foi adicionado

- backup lógico v2 com contagem e SHA-256 por tabela;
- criptografia Fernet para cópias automáticas;
- verificação de integridade do arquivo;
- restauração transacional em banco separado;
- proteção contra restauração no mesmo banco de origem;
- ajuste das sequences do PostgreSQL após restauração;
- workflow diário do GitHub Actions para backup criptografado offsite por 30 dias;
- workflow manual de restore drill;
- `.env.example` sem segredos reais;
- documentação de recuperação de desastre.

## Secrets necessários no GitHub

Em **Settings → Secrets and variables → Actions**, cadastrar:

- `BACKUP_DATABASE_URL`: External Database URL do PostgreSQL de produção;
- `BACKUP_ENCRYPTION_KEY`: chave gerada por `python scripts/generate_backup_key.py`;
- `RESTORE_TEST_DATABASE_URL`: URL de um PostgreSQL separado e descartável, usada apenas no restore drill.

Nunca colocar esses valores no código, README, chat público ou commit.

## Backup diário

O workflow `.github/workflows/database-backup.yml` roda diariamente às 03:15 UTC e também pode ser executado manualmente. A cópia é criptografada antes de ser enviada como artifact e fica retida por 30 dias.

## Restore drill

O workflow `.github/workflows/restore-drill.yml` é manual porque ele limpa o banco configurado em `RESTORE_TEST_DATABASE_URL`. Ele cria um backup novo, verifica hashes, aplica migrations no banco de teste, restaura os registros e compara as contagens.

**Nunca usar a URL de produção em `RESTORE_TEST_DATABASE_URL`.** O script também compara fingerprints e recusa o mesmo banco de origem quando o backup v2 contém essa informação.

## Limite importante

Esse mecanismo é uma camada extra de proteção da aplicação. Para operação comercial madura, manter também backup/snapshot/PITR gerenciado pelo provedor PostgreSQL. GitHub Actions artifacts não substituem um serviço de backup gerenciado de longo prazo.

## Validação feita antes da entrega

- auditoria estrutural da Fase 24.3: **11 OK, 0 avisos, 0 erros**;
- compilação Python concluída sem erro;
- backup v2 criptografado criado em banco SQLite de teste;
- verificação de hashes concluída;
- restauração em segundo banco SQLite concluída e contagens conferidas;
- proteção contra restaurar no mesmo banco de origem testada e bloqueada corretamente.

O restore real em PostgreSQL separado continua como etapa operacional obrigatória após a configuração de `RESTORE_TEST_DATABASE_URL`.
