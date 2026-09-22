# Catálogo Digital — pacote completo (backend + frontend)

Este pacote contém:
- `backend/` — API FastAPI, sem alterações de código (as correções que discutimos, como paginação, ainda **não** foram aplicadas).
- `frontend/` — a versão com a nova identidade visual (cores, tipografia, remoção dos clichês de "SaaS genérico").
- `docs/` — documentação original do projeto (arquitetura, roadmap, status).

O que **não** está aqui, de propósito:
- `backend/.env` — continha segredos reais (`JWT_SECRET`, senha do banco, chaves do Mercado Pago). Você precisa recriá-lo com valores novos (veja o passo 2) — **não reaproveite os valores do `.env` que você me enviou antes**, rotacione-os.
- `backend/.venv`, `.git`, `backups/`, arquivos `.db` — ambiente local antigo e histórico do Git, que você já tem na sua máquina.

---

## 1. Pré-requisitos

- Python 3.11+ instalado
- Node não é necessário (o frontend é HTML/CSS/JS puro, sem build)

## 2. Subir o backend localmente

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

# crie o .env a partir do exemplo
cp .env.example .env
```

Abra `backend/.env` e ajuste pelo menos:
- `JWT_SECRET` → gere um valor novo e forte:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
- `DATABASE_URL` → para testar localmente, o padrão `sqlite:///./catalogo.db` já funciona. Para produção, é obrigatório PostgreSQL (o próprio `config.py` bloqueia SQLite em produção).
- `CORS_ORIGINS` → mantenha `http://127.0.0.1:5500,http://localhost:5500` para desenvolvimento local (ajuste a porta se usar outra).

Depois, aplique as migrations e (opcionalmente) popule dados de demonstração:

```bash
alembic upgrade head
python seed.py          # cria lojas de exemplo (mercado, barbearia, pousada etc.)
```

Suba o servidor:

```bash
uvicorn app.main:app --reload --port 8000
```

Teste em `http://127.0.0.1:8000/api/health` — deve responder `{"status":"ok", ...}`.

## 3. Abrir o frontend

O frontend detecta automaticamente `http://127.0.0.1:8000` quando aberto como arquivo local ou em `localhost`/`127.0.0.1` — não precisa configurar nada.

**Opção simples:** abra `frontend/index.html` direto no navegador (duplo clique).

**Opção recomendada** (evita bloqueios do navegador para alguns recursos): sirva a pasta como estático:

```bash
cd frontend
python -m http.server 5500
```

e acesse `http://127.0.0.1:5500`.

Páginas principais:
- `index.html` — landing / apresentação
- `loja.html?slug=mercado-bom-preco` — vitrine pública de uma loja (troque o `slug` pelas lojas criadas no `seed.py`)
- `admin.html` — painel da loja (login com o usuário criado pelo seed)
- `super-admin.html` — painel do dono da plataforma
- `cliente.html` — área do cliente final

## 4. O que mudou nesta entrega

- **Frontend:** nova paleta (cobre/tinta em vez do roxo genérico), tipografia própria (Manrope + Inter), raios e sombras mais discretos, ícones/emoji trocados por monogramas — detalhado na mensagem anterior.
- **Backend:** nenhuma alteração de código ainda. A revisão que fizemos identificou o backend como maduro e sem falhas de segurança nos módulos auditados (autenticação, isolamento multi-loja, upload de imagens, assinatura de webhook do Mercado Pago, preços calculados no servidor). O único ponto pendente é **paginação** nas listagens administrativas (`/admin/orders`, `/admin/products`, `/admin/inventory`) — ainda não implementada, à sua espera de sinal verde.

## 5. Antes de ir para produção

- Rotacione `JWT_SECRET` e qualquer chave do Mercado Pago que estava no `.env` antigo enviado no chat.
- Em produção, `ENVIRONMENT=production` ativa validações automáticas: exige HTTPS em `CORS_ORIGINS`, bloqueia SQLite, exige `JWT_SECRET` forte etc. Se alguma faltar, o app recusa subir (`settings.validate_for_runtime()`) — é proposital, não é bug.
- Consulte `docs/PLANO_RECUPERACAO_DESASTRE.md` para backup/restore e `README.md` para o fluxo de release gate já existente no projeto.
