# Status atual — Catálogo Digital

Versão consolidada até a **Fase 24.2**.

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
- cupons por produto no Admin e cálculo restrito aos itens elegíveis;
- cupons de planos SaaS gerenciados pelo Super Admin e aplicáveis na escolha de plano do Admin.

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

## Fase 23.4 — cupons avançados e cupons de planos

- cupons de loja podem valer para pedido inteiro ou produtos selecionados;
- Produtos do Admin possuem atalho para criar cupom do item;
- Super Admin controla cupons comerciais dos planos SaaS;
- Admin pode escolher plano, aplicar código e visualizar subtotal/desconto/total;
- fatura de troca fica pendente até confirmação do pagamento;
- cupons recorrentes podem ser reaplicados às renovações enquanto válidos;
- migration `015_advanced_coupons`;
- backend `23.4.0`.


## Fase 24.1 — auditoria automatizada e hardening

- hardening de autenticação, CORS, cache sensível, request IDs e rate limit;
- versão centralizada em `backend/app/version.py`;
- auditoria local automatizada de sintaxe, migrations, segredos e guardas;
- smoke test público do deploy;
- verificador estrutural dos backups lógicos;
- sem migration; backend `24.1.0`.

### Evolução da Fase 24

Os testes autenticados de isolamento e a regressão funcional passam a ser cobertos pela Fase 24.2. Permanecem restore drill, automação/offsite de backup, rotações finais de credenciais e revisão manual multi-dispositivo.


## Fase 24.2 — regressão funcional e multi-tenant

- regressão automatizada em banco SQLite temporário;
- login e papéis validados;
- isolamento Mercado x Loja Tech validado por listagem e acesso direto;
- guardas Admin x Super Admin validadas;
- fluxos públicos de varejo, agendamento, reserva e locação validados;
- edição de loja pelo Super Admin validada;
- cupom por produto com bloqueio cross-tenant validado;
- cupom de plano Super Admin → Admin validado;
- assinatura e central de cobrança validadas em modo leitura;
- sem migration; backend `24.2.0`.

### Ainda pendente dentro da Fase 24

- restore drill real em banco separado;
- automação/offsite de backup;
- rotação final de credenciais sensíveis antes do lançamento;
- revisão final manual em celular/tablet/desktop das telas principais.
