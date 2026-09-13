# Status atual — Catálogo Digital

Versão consolidada até a **Fase 24.7.5**.

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

Mercado Pago passa a ser o primeiro gateway real da cobrança SaaS, inicialmente com Pix imediato. O Access Token e o segredo do webhook ficam somente no backend. Pix Automático, PicPay e outros continuam previstos pela mesma arquitetura.

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

Após publicar e validar a Fase 24.7, configurar as credenciais do Mercado Pago no Render e executar um pagamento Pix real controlado. Depois seguir para chatbot/WhatsApp, pagamentos dos clientes das lojas e preparação final de lançamento.


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


## Fase 24.5.1 — refinamento visual pré-lançamento

- dashboard da loja simplificado, sem o bloco de ações rápidas;
- navegação mobile convertida para sidebar recolhível;
- botões com feedback visual mais rico e acessível;
- tema por loja expandido para mais componentes;
- nova identificação personalizável do painel (`panel_brand_name` e `panel_logo_url`), com upload via storage/Cloudinary;
- área pública simplificada, removendo blocos genéricos de texto promocional;
- migration `016_admin_branding`; backend `24.5.1`.


## Fase 24.6 — Portal do Cliente, rastreamento e refinamentos finais

- nova conta de cliente final separada por loja (`customer_accounts`);
- login/cadastro do cliente sem compartilhar sessão com Admin/Super Admin;
- histórico autenticado de pedidos e agendamentos;
- token público seguro adicionado a pedidos para acompanhamento sem login;
- página unificada `acompanhar.html` para pedido/agendamento;
- criação de conta a partir do link de acompanhamento para vincular histórico com posse do token;
- respostas públicas de agendamento deixam de expor e-mail/telefone do cliente;
- cartões de métricas recebem ícones semânticos mais claros no Admin e Super Admin;
- ações dos produtos ficam organizadas em grade e seguem a temática da loja;
- sidebar do Admin pode ser recolhida no desktop/notebook e mantém o drawer no celular;
- migration `017_customer_portal`; backend `24.6.0`.

### Próxima fase

Fase 24.7 — preparação final de lançamento: domínio, SEO, PWA final, restore drill, credenciais/segredos e checklist comercial.


## Fase 24.6.1 — acabamento de navegação e login do cliente

- botão de recolher/expandir a sidebar do Admin reposicionado para fora da área rolável e com maior destaque visual;
- sidebar recolhida vira uma faixa mínima: oculta menus, loja e rodapé, preservando apenas a identificação principal e o botão de expansão;
- login/cadastro do cliente redesenhado como experiência premium dedicada, com identidade e cores da loja predominantes;
- login do cliente passa a ter hero temático, acompanhamento ilustrativo, campos refinados, mostrar/ocultar senha e botões mais interativos;
- acesso à conta fica disponível permanentemente no cabeçalho da loja, exibindo `Entrar` ou `Minha conta` conforme a sessão;
- backend em `24.6.1`; sem migration nova.

## Fase 24.6.2 — segmento Estamparia / Personalizados / Brindes

- categoria comercial nova para estamparia, sublimação, brindes e produtos personalizados;
- modelo operacional Híbrido;
- venda de produtos prontos com catálogo, carrinho, checkout e estoque;
- serviços personalizados e solicitações de orçamento no mesmo estabelecimento;
- pagamentos e entrega habilitados;
- cupons e promoções integrados quando liberados pelo plano;
- migration `018_personalizados_segment`; backend em `24.6.2`.



## Fase 24.6.3 — carrinho separado da vitrine

- catálogo público usa toda a largura disponível para produtos;
- carrinho não ocupa mais uma coluna fixa ao lado da vitrine;
- novo botão de carrinho no topo da navegação da loja, com ícone e contador;
- carrinho abre em drawer lateral responsivo com fechamento por botão, fundo ou tecla Esc;
- checkout e lógica do carrinho foram preservados;
- cache PWA atualizado para `catalogo-digital-v24-6-3`;
- sem nova migration; backend em `24.6.3`.


## Fase 24.7 — planos dinâmicos + cobrança SaaS via Pix

- planos Essencial, Profissional e Premium com valores iniciais de R$ 49,90, R$ 89,90 e R$ 149,90/mês;
- Super Admin pode editar preços, descrição, limites, recursos, período grátis, tolerância, destaque, ordem e disponibilidade;
- alterações de plano não mudam silenciosamente assinantes existentes graças ao snapshot comercial;
- Mercado Pago conectado ao backend para criação de Pix com QR Code/Copia e Cola;
- confirmação via consulta à API + webhook assinado;
- plano ativado somente após pagamento aprovado;
- desktop da loja pública ajustado para 3 produtos por linha;
- tipografia reforçada em toda a plataforma;
- migration `019_dynamic_plans_pix`; backend `24.7.2`; cache PWA `catalogo-digital-v24-7-0`.


## Hotfix 24.7.1 — Pix Mercado Pago via Orders API
- Pix SaaS migrado do endpoint legado `/v1/payments` para `/v1/orders`.
- Compatível com o cenário oficial de teste Pix do Mercado Pago (`test_user_br@testuser.com` + `first_name=APRO`).
- QR Code, Pix Copia e Cola e ticket passam a ser lidos de `transactions.payments[].payment_method`.
- Consulta de status passa a usar `GET /v1/orders/{id}`.
- Webhook aceita o tópico `order` e mantém compatibilidade com `payment` legado.
- Erros da API exibem detalhes melhores quando disponíveis.


## Hotfix 24.7.2 — teste Pix com valor predefinido
- Sandbox Pix por Orders usa R$ 50,00 apenas quando `MERCADO_PAGO_TEST_MODE=true` e o pagador é `test_user_br@testuser.com`.
- Fatura interna mantém o preço real do plano.
- Produção permanece protegida: a exceção de valor não é aceita com modo de teste desligado.


## Fase 24.7.3 — refatoração segura e manutenção

- comportamento funcional preservado;
- utilitários genéricos de DOM e formulários centralizados em `frontend/js/shared/dom-utils.js`;
- duplicações de helpers removidas das interfaces principais;
- `api.js` reorganizado em funções menores, constantes claras e tratamento de resposta isolado;
- tela de assinatura do Admin dividida em funções de renderização menores;
- acompanhamento público reformatado e separado em responsabilidades claras;
- imports Python sem uso removidos;
- scripts HTML, `.editorconfig` e cache PWA alinhados com a nova estrutura;
- sem migration; backend `24.7.3`; cache PWA `catalogo-digital-v24-7-3`.


## Fase 24.7.4 — acabamento visual premium

- nova camada visual compartilhada sem alteração funcional;
- tipografia, botões, cards, formulários, tabelas, modais e estados vazios refinados;
- Cliente, Admin e Super Admin mantêm a mesma identidade visual e maior consistência;
- responsividade preservada e reforçada;
- sem migration; backend `24.7.4`; cache PWA `catalogo-digital-v24-7-4`.


## Hotfix 24.7.5 — build do frontend no Render

- `frontend/render-build.sh` passa a copiar recursivamente a árvore de JavaScript;
- `frontend/js/shared/dom-utils.js` passa a ser publicado corretamente no Render;
- corrige falhas de carregamento que impediam login e funcionamento das lojas após a refatoração 24.7.3;
- cache PWA atualizado para forçar o carregamento dos assets corrigidos;
- sem migration; backend `24.7.5`.
