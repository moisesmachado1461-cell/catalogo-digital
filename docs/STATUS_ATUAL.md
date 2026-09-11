# Status atual — Catálogo Digital

Versão consolidada até a **Fase 22**.

## Concluído

- arquitetura SaaS multi-loja / multi-segmento;
- catálogo, pedidos, estoque, serviços, agendamentos e orçamentos;
- reservas e locações;
- pagamentos das lojas;
- planos e assinaturas;
- segurança/LGPD e relatórios;
- responsividade/PWA;
- GitHub + Render + PostgreSQL;
- Cloudinary persistente;
- backup lógico manual;
- Sentry/observabilidade;
- fundação multi-gateway;
- motor interno de cobrança, vencimentos, faturas, tolerância, cancelamento e troca de plano.

## Gateway real

A conexão com Mercado Pago ficou desacoplada por indisponibilidade temporária de uma conta elegível. Ela poderá ser adicionada depois sem refazer o motor de cobrança. Pix Automático, PicPay e outros continuam previstos pela mesma arquitetura.

## Próximo passo

**Fase 19.3 — Meu plano e cobrança + gestão financeira no Super Admin.**

Depois da Fase 19, iniciar a reformulação visual premium completa nas áreas do cliente, administrador e super administrador.


## Fase 19.3 — Meu Plano e Central de Cobrança
- Admin da loja: visão profissional do plano, uso, período, próxima cobrança, método e histórico de faturas.
- Super Admin: central financeira com assinaturas, faturas, status, gateways, registro manual de pagamento, cancelamento e processamento de vencimentos.
- Sem migration nesta fase.
- Gateway real continua pendente até uma conta elegível estar disponível.


## Fase 20 — Design System e identidade visual oficial

- Fundação visual compartilhada criada.
- Nova camada `design-system.css` aplicada a todas as páginas.
- `ui-system.js` adiciona microinterações e feedbacks sem alterar regras de negócio.
- Próximo: Fase 21 — reforma premium da área do cliente.


## Fase 21 — Área do Cliente Premium

- Loja pública reformulada com identidade própria, hero premium e cabeçalho orientado à marca da loja.
- Produtos, serviços, carrinho, filtros, contato, modais e experiência mobile refinados.
- Layout continua adaptado por capabilities para varejo, alimentação, serviços, reservas e locações.
- Sem migration.
- Fase 22 concluída: reformulação premium do Admin.


## Fase 22 — Admin Premium

- Login do administrador redesenhado.
- Navegação lateral agrupada por contexto operacional.
- Dashboard com saudação, plano, data e alertas contextuais.
- Cards de métricas e ações rápidas refinados.
- Cabeçalho, tabelas, formulários e modais com acabamento visual consistente.
- Melhor experiência em notebook, tablet e celular.
- Sem migration.
- Backend em `22.0.0`.
- Próximo: Fase 23 — Super Admin Premium.
