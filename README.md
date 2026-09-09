# Catálogo Digital — Fase 18

SaaS multi-loja e multi-segmento em HTML/CSS/JavaScript puro + FastAPI + SQLAlchemy/Alembic + PostgreSQL.

## Fase atual

**18 — Produção: armazenamento persistente, observabilidade, proteção operacional e backup**

A plataforma já está publicada com GitHub + Render + PostgreSQL. Esta fase fortalece a operação online e prepara uploads para armazenamento S3 compatível, como Cloudflare R2.

## Principais novidades

- storage `local` em desenvolvimento e `s3` em produção;
- suporte a Cloudflare R2/AWS S3;
- uploads WebP enviados ao storage externo;
- health check com banco + estado do storage;
- logs por requisição e `X-Request-ID`;
- integração opcional com Sentry;
- rate limit adicional nos endpoints de login;
- script de backup lógico do PostgreSQL;
- API `18.0.0`.

## Desenvolvimento local

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
python -m http.server 5500 --bind 0.0.0.0
```

Site: `http://127.0.0.1:5500`

API/Swagger: `http://127.0.0.1:8000/docs`

## Produção atual

- Frontend: Render Static Site
- Backend: Render Web Service
- Banco: Render PostgreSQL
- Código: GitHub privado

Consulte `docs/FASE_18_PRODUCAO_STORAGE_MONITORAMENTO.md`.

## Dados locais que devem ser preservados durante atualizações

```text
backend/.venv
backend/.env
backend/catalogo.db
backend/uploads
backend/backups
```

Esses itens não devem ser enviados ao GitHub.


## Fase 18.1 — Cloudinary

A produção também pode usar Cloudinary para imagens com `STORAGE_PROVIDER=cloudinary`. Veja `docs/FASE_18_CLOUDINARY.md`.
