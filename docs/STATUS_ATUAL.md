# Status atual — Catálogo Digital

Versão consolidada até a **Fase 23.3**.

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
- Super Admin Premium;
- perfil e segurança do Super Admin, com troca de e-mail/senha e revogação de outras sessões;
- edição completa das lojas pelo Super Admin;
- gestão e exposição pública controlada de cupons.

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


## Fase 23.1 — Perfil e Segurança do Super Admin

- alteração de nome e e-mail pelo próprio painel;
- confirmação da senha atual para troca de e-mail;
- troca de senha com política mínima de força;
- revogação das outras sessões por versão de token;
- renovação segura do JWT da sessão atual;
- auditoria das operações sensíveis;
- migration `013_super_admin_account_security`;
- backend em `23.1.0`.

## Fase 23.3 — Lojas e Cupons

- Fase 23.2 incorporada de forma cumulativa: edição completa de lojas no Super Admin;
- cupons podem ser criados/editados pelo Admin e pelo Super Admin;
- validade, limite, pedido mínimo, desconto máximo, ativação e visibilidade pública;
- nova seção de cupons na loja pública;
- cupons privados continuam ocultos;
- migration `014_public_coupons`;
- backend em `23.3.0`.

## Próximo passo

Fazer uma revisão integrada de **Cliente + Admin + Super Admin** para corrigir inconsistências visuais e funcionais remanescentes, seguida pela fase de testes finais, segurança, domínio/SEO/PWA e preparação comercial. A integração real com Mercado Pago pode ser retomada assim que houver um responsável adulto disponível para configurar a conta e as credenciais.


- Fase 23.2: edição completa de lojas restaurada no Super Admin.
