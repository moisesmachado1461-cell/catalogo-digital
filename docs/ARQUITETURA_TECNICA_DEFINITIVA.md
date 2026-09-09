# Catálogo Digital — Arquitetura Técnica Definitiva

Versão 1.0.

## Stack
Frontend: HTML5 + CSS3 + JavaScript puro.
Backend: Python + FastAPI.
Persistência: SQLAlchemy + Alembic.
Desenvolvimento: SQLite. Produção: PostgreSQL.
Autenticação: JWT.

## Arquitetura
SaaS multi-tenant com isolamento lógico por `store_id`. Cada negócio possui categoria, modelo de negócio e capacidades. Modelos iniciais: VAREJO, ALIMENTACAO, AGENDAMENTO, ORCAMENTO, RESERVA, LOCACAO, SERVICOS e HIBRIDO.

## Fundação implementada
`business_models`, `business_categories`, `stores` e `users`, com migration Alembic, seed de modelos/categorias, loja demonstrativa e autenticação inicial.

## Regra de segurança
O backend é a autoridade para tenant e permissões. O frontend nunca define livremente o `store_id` usado para autorizar operações.

## Próximas migrations
Catálogo, clientes, pedidos, estoque, serviços, profissionais, agendamentos, orçamentos, reservas, locações, cupons, promoções, pagamentos, planos e assinaturas.
