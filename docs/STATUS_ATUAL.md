# Status atual — Catálogo Digital

Versão consolidada até a **Fase 24.5.0**.

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

Executar uma vez o release gate local da Fase 24.5, enviar ao GitHub e confirmar o deploy com o smoke de produção. Depois, executar uma vez o workflow manual de restore drill no GitHub Actions. Com esses gates aprovados, avançar para domínio, SEO/PWA final e preparação comercial. A integração real com Mercado Pago continua desacoplada e pode ser retomada quando a conta e as credenciais estiverem disponíveis.


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

## Fase 24.3 — backup e recuperação

- backup lógico v2 com SHA-256 e contagens por tabela;
- criptografia Fernet para backups automáticos;
- backup diário offsite via GitHub Actions, após configuração dos secrets;
- retenção de 30 dias nos artifacts do workflow;
- restore seguro em banco separado com migrations, transação e ajuste de sequences;
- restore drill manual automatizado;
- plano de recuperação de desastre documentado;
- sem migration; backend `24.3.0`.

### Para concluir operacionalmente a Fase 24.3

Ainda é necessário cadastrar os secrets no GitHub e executar pelo menos um restore drill real em um PostgreSQL separado. Até esse teste real, a capacidade de restauração em PostgreSQL deve ser considerada preparada, mas não comprovada em produção.

## Fase 24.4 — revisão integrada Cliente + Admin + Super Admin

- auditoria estrutural dedicada às três superfícies principais;
- validação do Design System e CSS premium por área;
- conferência automatizada de viewport, runtime compartilhado e PWA;
- verificação das referências DOM estáticas e dinâmicas do frontend;
- validação de separação de papéis Admin x Super Admin no cliente;
- confirmação da arquitetura pública baseada em capabilities;
- sem migration; backend `24.4.1`.

### Ainda pendente antes do lançamento

- regressão funcional completa em ambiente com as dependências instaladas;
- restore drill real pelo workflow GitHub Actions com PostgreSQL temporário;
- revisão visual manual multi-dispositivo;
- rotação final das credenciais de produção;
- domínio, SEO/PWA final e checklist comercial.


## Correção 24.4.1 — reincorporação da Fase 24.3.1

- `restore-drill.yml` sobe PostgreSQL 18 temporário como service no GitHub Actions;
- não exige segundo PostgreSQL no Render;
- não exige o secret `RESTORE_TEST_DATABASE_URL`;
- continuam necessários `BACKUP_DATABASE_URL` e `BACKUP_ENCRYPTION_KEY`;
- o banco temporário é descartado ao final do workflow.


## Fase 24.5 — validação final de produção

- novo `phase24_5_release_gate.py` executa em um único comando a auditoria geral, revisão integrada e regressão funcional isolada;
- regressão funcional passa a validar dinamicamente a versão atual do backend, sem ficar presa à versão 24.2.0;
- auditoria e revisão integrada deixam de exigir números de versão codificados manualmente;
- `production_smoke_check.py` passa a usar por padrão as URLs oficiais do projeto;
- smoke de produção confirma versão esperada, ambiente production, banco, Cloudinary persistente/configurado, CORS, headers de segurança e páginas principais;
- sem migration; backend `24.5.0`.

### Gate operacional restante antes do lançamento

- executar `python backend\scripts\phase24_5_release_gate.py`;
- após o deploy, executar `python backend\scripts\production_smoke_check.py`;
- executar uma vez o workflow `Restore drill do PostgreSQL` no GitHub Actions;
- fazer apenas uma conferência visual curta da loja pública e dos painéis em desktop e celular.
