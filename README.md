# Catálogo Digital — Fase 24.6.0

SaaS multi-loja e multi-segmento em HTML/CSS/JavaScript puro + FastAPI + SQLAlchemy/Alembic + PostgreSQL.

## Fase atual

**24.6.0 — Portal do Cliente, acompanhamento e refinamentos finais de interface**

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

Consulte `docs/FASE_24_5_VALIDACAO_PRODUCAO.md` para o fluxo final de validação e deploy.

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

## Fase 24.3 — backup automático e recuperação de desastre

A proteção de dados recebeu backup lógico v2 verificável, criptografia para cópias automáticas, restore transacional em banco separado, workflow diário offsite e restore drill manual. Não há migration. Backend em `24.3.0`.


## Correção 24.4.1 — restore drill simplificado

A melhoria da Fase 24.3.1 foi reincorporada à base consolidada: o workflow manual de restore sobe um PostgreSQL 18 temporário no GitHub Actions. Assim, o teste não exige um segundo PostgreSQL no Render nem o secret `RESTORE_TEST_DATABASE_URL`.


## Fase 24.5 — validação final de produção

A validação foi simplificada para dois comandos:

Antes do push:

```powershell
python backend\scripts\phase24_5_release_gate.py
```

Depois que o Render ficar Live:

```powershell
python backend\scripts\production_smoke_check.py
```

O primeiro comando executa auditoria, revisão integrada e regressão funcional em banco temporário. O segundo confirma versão online, banco, Cloudinary persistente, CORS, headers de segurança e páginas públicas do deploy. Nenhuma migration foi adicionada. Backend base validado em `24.5.0`; refinamento visual atual em `24.5.1`.


## Fase 24.5.1 — refinamento visual pré-lançamento

- remove o bloco de ações rápidas do dashboard da loja;
- usa menu lateral recolhível também no celular;
- adiciona feedback visual/ripple aos botões com respeito a redução de movimento;
- amplia a aplicação das cores escolhidas pela loja em fundos, cards, navegação e estados interativos;
- permite definir nome e logo próprios para a identificação principal do painel;
- usa a logo real da loja no identificador lateral quando disponível e mantém iniciais como fallback;
- remove textos promocionais genéricos da área pública para priorizar produtos, serviços e informações úteis.


## Fase 24.6 — Portal do Cliente e acompanhamento

A experiência do cliente final agora possui identidade própria, sem misturar o acesso do cliente com o Admin da loja:

- conta de cliente separada por loja, com senha e sessão próprias;
- histórico autenticado de pedidos e agendamentos;
- link público seguro para acompanhar cada pedido por token não previsível;
- agendamentos passam a usar a mesma experiência unificada de acompanhamento;
- criação de conta pode ser feita a partir do link de um pedido/agendamento para vincular o histórico com segurança;
- página `cliente.html` para login/cadastro e `acompanhar.html` para status sem login;
- pedido mostra etapas de preparo, retirada ou entrega;
- agendamento mostra solicitado, confirmado e concluído/cancelado;
- migration `017_customer_portal` cria `customer_accounts` e adiciona `public_token` aos pedidos existentes e futuros;
- PWA/cache inclui as novas páginas;
- backend em `24.6.0`.

Também foram concluídos os refinamentos visuais solicitados antes do lançamento: ícones mais claros nos cards, ações de produto organizadas e tematizadas e sidebar recolhível no desktop/notebook.
