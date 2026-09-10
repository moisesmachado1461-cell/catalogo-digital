# Status atual — Catálogo Digital

## Versão

Fase 19.1 — Fundação da cobrança automática multi-gateway.

## Concluído antes desta fase

- backend FastAPI + SQLAlchemy + Alembic;
- frontend HTML/CSS/JavaScript;
- multi-loja / multi-tenant;
- catálogo, pedidos e estoque;
- serviços e agendamentos;
- orçamentos;
- reservas e locações;
- pagamentos dos clientes das lojas;
- planos e assinaturas administrados pela plataforma;
- segurança/LGPD;
- relatórios;
- responsividade/PWA;
- Render + PostgreSQL;
- Cloudinary;
- Sentry;
- backup lógico do banco.

## Fase 19.1

A cobrança da assinatura do SaaS passa a ter uma camada própria, separada dos pagamentos dos pedidos das lojas. A fundação aceita múltiplos provedores e registra preços externos, faturas e eventos de webhook de forma idempotente.

Provedores previstos inicialmente:

- Mercado Pago;
- Pix Automático;
- PicPay;
- controle manual para administração interna.

Nenhum gateway automático é marcado como disponível antes de existir uma integração real configurada.

## Próximo passo

Fase 19.2 — conectar o primeiro gateway real de assinatura recorrente e implementar checkout + webhook de produção.
