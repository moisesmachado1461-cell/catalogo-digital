# Catálogo Digital — Fase 17

SaaS multi-loja e multi-segmento em HTML/CSS/JavaScript puro + FastAPI + SQLAlchemy/Alembic.

## Fase atual

**17 — Preparação para GitHub, Render e PostgreSQL**

Além de todas as funcionalidades anteriores, esta versão está preparada para sair do `127.0.0.1` e ser publicada com frontend estático, API FastAPI e banco PostgreSQL.

## Desenvolvimento local

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
python -m http.server 5500 --bind 0.0.0.0
```

Site: `http://127.0.0.1:5500`

API/Swagger: `http://127.0.0.1:8000/docs`

## Produção

Consulte `docs/FASE_17_DEPLOY_GITHUB_RENDER.md`.

Arquitetura prevista:

```text
GitHub privado
├── Render Static Site (frontend)
├── Render Web Service (FastAPI)
└── Render PostgreSQL
```

## Dados locais que devem ser preservados durante atualizações

```text
backend/.venv
backend/.env
backend/catalogo.db
backend/uploads
```

Esses itens locais não devem ser enviados ao GitHub.
