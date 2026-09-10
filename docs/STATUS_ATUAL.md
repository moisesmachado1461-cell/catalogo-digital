# Status atual — Catálogo Digital

Versão consolidada até a **Fase 19.3**.

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
