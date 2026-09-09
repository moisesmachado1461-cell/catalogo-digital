# Fase 17 — GitHub + Render + PostgreSQL

## Objetivo
Publicar o Catálogo Digital na internet mantendo dois ambientes:

- desenvolvimento local: frontend `:5500`, backend `:8000`, SQLite;
- produção: frontend estático no Render, API FastAPI no Render e PostgreSQL gerenciado.

## O que esta fase prepara

- PostgreSQL via `psycopg`/SQLAlchemy;
- validação que impede SQLite quando `ENVIRONMENT=production`;
- `start-render.sh` aplica migrations e inicia Uvicorn usando a porta do Render;
- `.python-version` fixa Python 3.13 no backend;
- frontend recebe a URL da API em build time por `API_BASE_URL`;
- URLs relativas de imagens podem ser resolvidas contra a API;
- `RENDER_EXTERNAL_URL` pode ser usado automaticamente para URLs de uploads;
- `.gitignore` evita `.env`, bancos locais, venv, uploads e temporários no GitHub.

## Arquitetura de produção

```text
GitHub privado
   ├── frontend -> Render Static Site -> HTTPS
   └── backend  -> Render Web Service -> FastAPI
                                      -> Render PostgreSQL
```

## Configuração do backend no Render

Root Directory:

```text
backend
```

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
bash start-render.sh
```

Health Check Path:

```text
/api/health
```

Variáveis:

```text
ENVIRONMENT=production
DATABASE_URL=<Internal Database URL do Render PostgreSQL>
JWT_SECRET=<segredo aleatório com 32+ caracteres>
CORS_ORIGINS=https://SEU-FRONTEND.onrender.com
```

## Configuração do frontend no Render

Root Directory:

```text
frontend
```

Build Command:

```text
bash render-build.sh
```

Publish Directory:

```text
dist
```

Variável de build:

```text
API_BASE_URL=https://SEU-BACKEND.onrender.com
```

## Banco

O banco local `catalogo.db` não deve ser enviado ao GitHub. O banco online é criado por migrations do Alembic no PostgreSQL.

Para a primeira demonstração online, você pode rodar o seed no ambiente de produção conscientemente. Não use credenciais de demonstração como credenciais comerciais permanentes.

## Uploads

Render Web Services usam filesystem efêmero por padrão. Para um teste inicial, uploads podem desaparecer após reinício/redeploy. Para uso comercial, usar uma destas opções:

1. Persistent Disk do Render e `UPLOAD_DIR=/var/data/uploads`; ou
2. storage de objetos (S3/R2 ou equivalente), preferível quando quisermos escalar.

Não tratar a pasta local `backend/uploads` como armazenamento comercial definitivo.

## Ordem de publicação

1. enviar o código para GitHub privado;
2. criar PostgreSQL no Render;
3. criar Web Service do backend;
4. configurar `DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT` e CORS temporário/exato;
5. confirmar `/api/health` online;
6. criar Static Site do frontend;
7. configurar `API_BASE_URL` com a URL do backend;
8. atualizar `CORS_ORIGINS` do backend com a URL exata do frontend;
9. testar pelo celular com Wi‑Fi desligado (4G/5G);
10. depois decidir storage persistente e domínio.

## Regra de segurança

Nunca colocar no GitHub:

- `.env`;
- `JWT_SECRET` real;
- senha/URL externa do PostgreSQL;
- tokens de gateway;
- chaves privadas.
