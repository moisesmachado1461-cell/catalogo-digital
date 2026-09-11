# Status atual — Catálogo Digital

Versão consolidada até a **Fase 23**.

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
- motor interno de cobrança, vencimentos, faturas, tolerância, cancelamento e troca de plano;
- Meu Plano e Central de Cobrança;
- Design System oficial;
- área do cliente premium;
- Admin Premium;
- Super Admin Premium.

## Gateway real

A conexão com Mercado Pago continua desacoplada e pode ser adicionada posteriormente, com uma conta elegível e autorizada, sem reconstruir o motor de cobrança. Pix Automático, PicPay e outros continuam previstos pela mesma arquitetura.

## Fase 23 — Super Admin Premium

- Login e navegação central redesenhados.
- Dashboard executivo com indicadores e visão operacional.
- Busca e filtro na gestão de lojas.
- Planos apresentados como cards comerciais.
- Cobrança SaaS visualmente refinada.
- Formulários e modais reorganizados.
- Melhor uso em notebook, tablet e celular.
- Sem migration.
- Backend em `23.0.0`.

## Próximo passo

Fazer uma revisão integrada de **Cliente + Admin + Super Admin** para corrigir inconsistências visuais e funcionais remanescentes, seguida pela fase de testes finais, segurança, domínio/SEO/PWA e preparação comercial. A integração real com Mercado Pago pode ser retomada assim que houver um responsável adulto disponível para configurar a conta e as credenciais.
