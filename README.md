# Catálogo Digital — Fase 19.2

SaaS multi-loja e multi-segmento em HTML/CSS/JavaScript puro + FastAPI + SQLAlchemy/Alembic + PostgreSQL.

## Fase atual

**19.2 — Motor interno de cobrança e ciclo de assinaturas**

A plataforma mantém separadas as duas áreas financeiras:

- `payments`: pagamentos dos clientes finais para cada loja;
- `billing`: mensalidade que a loja paga para usar o Catálogo Digital.

## O que já está em produção

- multi-tenant;
- catálogo, carrinho, pedidos e estoque;
- serviços e agendamentos;
- orçamentos;
- reservas e locações;
- pagamentos manuais das lojas;
- planos e assinaturas;
- segurança/LGPD;
- relatórios;
- responsividade/PWA;
- PostgreSQL + Render;
- Cloudinary para imagens persistentes;
- Sentry/observabilidade;
- fundação de cobrança multi-gateway.

## Novidades da Fase 19.2

- faturas de renovação idempotentes;
- ciclo mensal/anual;
- vencimento e próxima cobrança;
- período de tolerância;
- `PAST_DUE` e `EXPIRED`;
- confirmação/falha manual de pagamento;
- cancelamento imediato ou no final do período;
- troca de plano somente após confirmação do pagamento;
- auditoria das operações financeiras;
- script repetível para processamento do ciclo de cobrança.

Nenhum banco/gateway externo é simulado nesta fase. Mercado Pago, Pix Automático e PicPay continuam desacoplados e serão conectados por adaptadores próprios quando houver credenciais elegíveis.

## Desenvolvimento local

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
python -m http.server 5500 --bind 0.0.0.0
```

## Produção

- Frontend: Render Static Site
- Backend: Render Web Service
- Banco: Render PostgreSQL
- Código: GitHub privado

Consulte `docs/FASE_19_2_MOTOR_ASSINATURAS.md`.

## Dados locais que nunca devem ir para o GitHub

```text
backend/.venv
backend/.env
backend/catalogo.db
backend/uploads
backend/backups
```


## Fase 19.3 — Plano e cobrança
O Admin possui visão detalhada da própria assinatura e o Super Admin possui uma Central de Cobrança operacional. O primeiro gateway automático real permanece desacoplado e será conectado depois.
