# Fase 18 — Produção: armazenamento persistente, observabilidade e backups

## Objetivo

A Fase 18 remove um dos principais riscos do ambiente online atual: uploads dependerem do disco temporário do servidor. Também melhora logs, monitoramento, proteção de login e cria uma rotina de backup lógico.

## 1. Armazenamento de imagens

O backend agora possui uma abstração de armazenamento com dois modos:

- `STORAGE_PROVIDER=local`: desenvolvimento local, usando `backend/uploads`.
- `STORAGE_PROVIDER=s3`: produção, usando um serviço compatível com S3, como Cloudflare R2 ou AWS S3.

Novos uploads continuam sendo redimensionados e convertidos para WebP antes de serem enviados ao provedor externo.

Variáveis para S3/R2:

```text
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=...
S3_REGION=auto
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=...
S3_PUBLIC_BASE_URL=...
```

Nunca coloque `S3_ACCESS_KEY_ID` ou `S3_SECRET_ACCESS_KEY` no GitHub.

### Arquivos antigos

Arquivos já existentes em `backend/uploads` não são enviados automaticamente para o armazenamento externo. Depois de configurar o bucket, reenvie pelo painel as imagens importantes (logo, banner, serviços, produtos e profissionais) ou faça uma migração dedicada.

## 2. Health check melhorado

`GET /api/health` agora informa:

- versão da API;
- status do PostgreSQL;
- provedor de storage;
- se o storage é persistente.

Em produção com `STORAGE_PROVIDER=local`, o sistema continua funcionando, porém o health deixa explícito que o armazenamento não é persistente.

## 3. Observabilidade

Há logs de requisição com:

- método HTTP;
- caminho;
- status;
- duração;
- `X-Request-ID`.

Sentry é opcional. Se `SENTRY_DSN` for configurado, exceções podem ser acompanhadas sem enviar PII por padrão.

Variáveis:

```text
SENTRY_DSN=...
SENTRY_TRACES_SAMPLE_RATE=0.05
LOG_LEVEL=INFO
```

## 4. Rate limit de login

Além do bloqueio por tentativas de senha, `/api/auth/login` e `/api/auth/token` têm limite por IP em memória.

```text
LOGIN_RATE_LIMIT_PER_MINUTE=15
```

Esse limite é adequado para a instância única atual. Quando houver múltiplas instâncias, o contador deverá migrar para Redis ou outro armazenamento compartilhado.

## 5. Backup lógico

Foi adicionado:

```text
backend/scripts/backup_database.py
```

Ele cria um backup `.json.gz` do PostgreSQL usando a `External Database URL` informada de forma oculta.

Execução:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/backup_database.py
```

O resultado vai para:

```text
backend/backups/
```

Essa pasta é ignorada pelo Git.

Esse backup é uma camada extra de segurança. Para clientes comerciais, o PostgreSQL deverá usar também backups automáticos gerenciados pela infraestrutura.

## 6. Dependências novas

```text
boto3
sentry-sdk[fastapi]
```

Depois de instalar esta fase:

```powershell
pip install -r requirements.txt
```

## 7. Banco de dados

Não há nova migration nesta fase. A versão do Alembic continua:

```text
010_security_lgpd (head)
```

## 8. Versão

API: `18.0.0`

## Próxima sequência recomendada

1. instalar a Fase 18 localmente;
2. enviar a alteração ao GitHub;
3. deixar o Render redeployar;
4. criar/configurar um bucket persistente de imagens;
5. cadastrar as variáveis de storage no Render;
6. testar upload de uma imagem nova;
7. executar um backup lógico do PostgreSQL;
8. configurar monitoramento externo antes do lançamento comercial.
