# Catálogo Digital — Fase 22

SaaS multi-loja e multi-segmento em HTML/CSS/JavaScript puro + FastAPI + SQLAlchemy/Alembic + PostgreSQL.

## Fase atual

**22.0 — Admin Premium**

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


## Fase 20 — Design System

A base visual oficial do produto está em `frontend/css/design-system.css`, com comportamento compartilhado em `frontend/js/ui-system.js`. A versão do backend é 20.0.0.


## Fase 21 — Área do Cliente Premium
A experiência pública das lojas recebeu uma reformulação visual completa e responsiva, preservando os fluxos funcionais existentes.


## Fase 22 — Admin Premium

O painel do administrador da loja foi reformulado com foco em uso diário, clareza e acabamento comercial:

- login profissional e responsivo;
- sidebar organizada por grupos;
- ícones locais para navegação funcional;
- cabeçalho com identidade do administrador;
- cartão de boas-vindas e resumo contextual;
- alertas operacionais de pedidos, agenda, estoque e pagamentos;
- métricas com hierarquia visual aprimorada;
- ações rápidas com contexto;
- tabelas, formulários, modais e responsividade refinados;
- cache PWA atualizado para a versão 22.

Nenhuma regra de negócio ou isolamento multi-tenant foi removido. Não há migration nesta fase.

## Fase 23 — Super Admin Premium

O painel central da plataforma foi reformulado para o mesmo padrão visual premium das áreas do cliente e do administrador:

- login premium e responsivo;
- sidebar organizada por visão geral e comercial;
- dashboard executivo com métricas e resumo da saúde da plataforma;
- busca e filtro de lojas;
- cards comerciais para planos;
- central de cobrança refinada;
- modais e formulários reorganizados;
- responsividade aprimorada;
- cache PWA atualizado.

Não há migration nesta fase. Backend em `23.1.0`.


## Fase 23.1 — Perfil e Segurança do Super Admin

O Super Admin agora pode gerenciar a própria conta em uma área dedicada:

- alterar nome;
- alterar e-mail com confirmação da senha atual;
- alterar senha;
- encerrar outras sessões;
- manter a sessão atual com novo token;
- registrar as operações sensíveis em auditoria.

A migration `013_super_admin_account_security` adiciona versionamento de tokens à tabela `users`.
Backend em `23.1.0`.


## Fase 23.2 — edição de lojas no Super Admin
O Super Admin volta a editar dados completos das lojas pelo painel, preservando store_id e histórico.

## Fase 23.3 — lojas e cupons
Atualização cumulativa que mantém a edição de lojas e amplia cupons no Admin, Super Admin e loja pública. Cupons só aparecem publicamente quando marcados como visíveis. A migration `014_public_coupons` adiciona esse controle de exposição. Backend em `23.3.0`.

## Fase 23.4 — cupons avançados e cupons de planos

Os cupons das lojas agora podem ser limitados a produtos selecionados, inclusive
por atalho na tela de Produtos do Admin. A cobrança SaaS ganhou um sistema de
cupons separado, controlado pelo Super Admin, com elegibilidade por plano,
percentual/valor fixo, validade, limite de usos e duração na primeira fatura ou
recorrente. O Admin pode escolher um plano em Meu plano, validar o cupom e gerar
a fatura de troca. Backend em `23.4.0`; migration `015_advanced_coupons`.


## Fase 24.1 — auditoria e hardening

A primeira etapa da revisão final adiciona hardening de autenticação/configuração, auditoria automatizada do projeto, smoke test público do deploy e verificação estrutural de backups. Não há migration. Backend em `24.1.0`.


## Fase 24.2 — testes funcionais e isolamento multi-tenant

A regressão funcional automatizada usa um banco temporário e valida login, papéis, isolamento entre duas lojas, acesso cruzado, fluxos públicos por segmento, edição de loja, cupons por produto, cupons de planos e áreas de assinatura/cobrança. Não há migration. Backend em `24.2.0`.
