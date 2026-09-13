# Catálogo Digital — Fase 24.9.3

SaaS multi-loja e multi-segmento em HTML/CSS/JavaScript puro + FastAPI + SQLAlchemy/Alembic + PostgreSQL.

## Fase atual

**24.9.3 — Correção da troca OAuth do Marketplace**

A plataforma mantém separadas as duas áreas financeiras:

- `payments`: pagamentos dos clientes finais para cada loja;
- `billing`: mensalidade que a loja paga para usar o Catálogo Digital.




## Fase 24.9.3 — correção da troca OAuth do Marketplace

- envia `test_token` no formato textual esperado pela API OAuth (`"true"` / `"false"`);
- mantém PKCE S256 com `code_verifier` na troca por Access Token;
- preserva a mensagem sanitizada devolvida pelo Mercado Pago quando `/oauth/token` recusa a conexão;
- o Admin diferencia `invalid_client`, `invalid_grant`, `unauthorized_client` e `invalid_request`;
- nenhum segredo, token ou payload bruto é exposto ao frontend;
- nenhuma migration nova.

## Fase 24.9.2 — correção OAuth/PKCE do Marketplace

- corrige o parâmetro PKCE enviado ao Mercado Pago de `code_challenge_method` para `code_method`, conforme a documentação atual do OAuth;
- mantém `S256`, `state` e Redirect URI existentes;
- melhora a mensagem de retorno quando a autorização OAuth falha;
- nenhuma migration nova.

## Fase 24.9.0 — Pagamentos online dos clientes das lojas

- cada loja conecta a própria conta Mercado Pago por OAuth/PKCE;
- Access Token e refresh token do vendedor ficam criptografados no banco;
- o dinheiro do cliente final vai direto para a conta Mercado Pago da própria loja;
- Pix online é exibido apenas para planos com `online_payments` e lojas conectadas;
- checkout de pedidos, agendamentos, reservas e locações aceita Pix online;
- QR Code e Pix Copia e Cola aparecem no site e podem ser retomados no acompanhamento;
- webhook atualiza o pagamento automaticamente;
- pagamentos online não podem ser marcados manualmente como pagos pelo Admin;
- Pix manual, dinheiro, cartão na entrega e WhatsApp continuam disponíveis;
- migration `020_store_marketplace_payments`;
- backend `24.9.3`.

A cobrança da assinatura SaaS continua totalmente separada dos pagamentos dos clientes das lojas.

## Fase 24.8.3 — IA objetiva em português e raciocínio oculto

- respostas sempre orientadas a português do Brasil;
- Qwen/Groq usa `reasoning_effort=none` e `reasoning_format=hidden`;
- blocos `<think>` são removidos no backend como defesa adicional;
- respostas limitadas e mais objetivas para atendimento;
- nenhuma migration e nenhuma biblioteca nova.

## Fase 24.8.2 — base de conhecimento automática da IA

A Fase 24.8.2 centraliza o conhecimento do assistente no backend e elimina a necessidade de treinar o modelo novamente a cada evolução do produto.

- fonte oficial única em `backend/app/assistant_knowledge.json`;
- o backend recarrega automaticamente a base quando o arquivo muda;
- recuperação contextual por área, seção, palavras-chave e conteúdo;
- a IA recebe apenas os tópicos oficiais mais relevantes para cada pergunta;
- o frontend não é mais fonte confiável de conhecimento para a IA;
- `assistant-knowledge.js` passa a ser apenas um fallback gerado para a interface;
- script `backend/scripts/sync_assistant_knowledge.py` mantém o fallback do frontend sincronizado com a fonte oficial;
- endpoint `GET /api/assistant/knowledge/status` informa versão e quantidade de tópicos carregados;
- nenhuma migration e nenhuma biblioteca nova.

Nas próximas fases, novas funcionalidades devem atualizar a fonte oficial de conhecimento junto da documentação da feature. A IA passa a conhecer a mudança no próximo deploy, sem treinamento adicional.

## Fase 24.8.1 — IA contextual e objetiva

A Fase 24.8.1 evolui o assistente local para uma arquitetura híbrida: IA quando configurada e base local como fallback.

- endpoint seguro `POST /api/assistant/chat` no backend;
- integração compatível com provedores que usam o formato Chat Completions;
- chave da IA permanece somente no Render/backend;
- contexto automático de Cliente, Admin, Super Admin e loja pública;
- busca local seleciona apenas trechos relevantes da base oficial antes de consultar a IA;
- respostas curtas e focadas no uso do Catálogo Digital;
- histórico curto da conversa para perguntas de continuação;
- limite de requisições por minuto para reduzir abuso/custo;
- fallback automático para o assistente local quando a IA estiver indisponível;
- nenhum dado sensível, senha, token ou segredo é enviado pelo frontend;
- nenhuma migration nesta fase.

A IA fica desativada por padrão até que `ASSISTANT_AI_ENABLED=true` e as credenciais do provedor sejam configuradas no backend.

## Fase 24.8.0 — Assistente contextual do Catálogo Digital

A Fase 24.8.0 adiciona um assistente de ajuda embutido no site, sem dependência de IA paga ou biblioteca externa.

- botão flutuante premium nas áreas principais;
- respostas sobre funcionalidades do Cliente, Admin e Super Admin;
- contexto automático da tela atual;
- sugestões rápidas conforme a área aberta;
- base de conhecimento local e versionada;
- nenhuma leitura de senha, token ou dado sensível;
- WhatsApp detectado na loja quando houver canal oficial publicado;
- estrutura pronta para a futura integração oficial do mesmo conhecimento com WhatsApp Business.

Não há migration nesta fase.

## Fase 24.7.7 — pagamento Pix pendente acessível

- `Meu plano` destaca cobranças Pix pendentes válidas.
- O lojista pode reabrir o mesmo QR Code pelo botão **Ver QR Code**, sem gerar nova cobrança.
- O histórico financeiro também oferece acesso à cobrança pendente.
- Ao reabrir, o sistema consulta o status atual no backend e retoma a verificação automática.
- Nenhuma migration nova e nenhuma mudança na regra de negócio do Mercado Pago.


## Fase 24.7.6 — diagnóstico Pix em produção

- mantém a lógica de cobrança inalterada;
- melhora a leitura dos erros HTTP 400 devolvidos pela Orders API;
- mostra código, mensagem e campo inválido quando o Mercado Pago os informa;
- não exibe Access Token, segredo de webhook nem valores sensíveis do payload.


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

A Fase 24.7 conecta o primeiro gateway real: Mercado Pago para Pix imediato da mensalidade SaaS. Pix Automático, PicPay e outros permanecem previstos pela arquitetura multi-gateway.

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
O Admin possui visão detalhada da própria assinatura e o Super Admin possui uma Central de Cobrança operacional. O primeiro gateway real, Mercado Pago via Pix imediato, é conectado na Fase 24.7.


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


## Fase 24.6.1 — experiência do cliente e sidebar

Refinamento visual sem migration: a sidebar recolhida do Admin agora ocupa o mínimo possível e não exibe as opções do menu; o controle de expandir/recolher fica mais visível e fora da área rolável. A área do cliente ganhou uma tela de login/cadastro própria, premium, interativa e fortemente tematizada com as cores e logo da loja. O acesso `Entrar / Minha conta` permanece disponível diretamente no cabeçalho da loja, sem depender do checkout. Backend em `24.6.1`.

## Fase 24.6.2 — Estamparia, Personalizados e Brindes

Novo segmento comercial baseado no modelo Híbrido, preparado para negócios que vendem produtos prontos e também trabalham com personalização e encomendas sob orçamento. O segmento habilita catálogo, carrinho, checkout, estoque, serviços, orçamentos, pagamentos, entrega, cupons e promoções conforme o plano. Migration `018_personalizados_segment`; backend em `24.6.2`.



## Fase 24.6.3 — Carrinho separado da vitrine pública

A vitrine de produtos passa a ocupar toda a largura útil da loja. O carrinho deixa de ocupar uma coluna fixa ao lado dos produtos e passa a ser acessado por um botão temático no topo, com ícone e contador de itens. Ao clicar, abre um drawer lateral responsivo para revisar itens e finalizar o pedido. O comportamento vale para desktop e celular, mantendo a temática de cores da loja e liberando mais espaço para o catálogo. Sem nova migration; backend em `24.6.3`.


## Fase 24.7 — Planos dinâmicos + Pix imediato

- três planos comerciais iniciais: Essencial R$ 49,90, Profissional R$ 89,90 e Premium R$ 149,90;
- preços, limites, recursos, teste, tolerância, selo, destaque, ordem e disponibilidade editáveis pelo Super Admin;
- plano Gratuito mantido apenas como contingência interna;
- snapshot das condições comerciais protege assinantes existentes contra alterações silenciosas de preço;
- Mercado Pago conectado para Pix imediato com QR Code e Copia e Cola;
- idempotência, validação de webhook e reconciliação do pagamento antes de ativar o plano;
- vitrine desktop com 3 produtos por linha;
- tipografia mais robusta em Cliente, Admin e Super Admin;
- migration `019_dynamic_plans_pix`; backend `24.7.2`.

Veja `docs/FASE_24_7_PLANOS_PIX_MERCADO_PAGO.md`.


## Hotfix 24.7.2 — sandbox Pix oficial
- modo de teste explícito via `MERCADO_PAGO_TEST_MODE`;
- cenário `test_user_br@testuser.com` usa os R$ 50,00 predefinidos pelo sandbox oficial;
- valor comercial da fatura permanece inalterado;
- mensagens de erro do gateway exibem código/HTTP quando disponível.


## Fase 24.7.3 — refatoração segura e limpeza

Sem mudança de regra de negócio ou funcionalidade:

- utilitários DOM/form compartilhados em `frontend/js/shared/dom-utils.js`;
- remoção de helpers duplicados entre Cliente, Loja, Admin e Super Admin;
- `frontend/js/api.js` dividido em funções menores e constantes nomeadas;
- renderização de assinatura do Admin dividida em funções menores e focadas;
- acompanhamento de pedidos/agendamentos reformatado e organizado;
- importações Python não utilizadas removidas;
- scripts HTML padronizados, `.editorconfig` adicionado e cache PWA atualizado;
- sem migration nova; backend `24.7.3`.


## Fase 24.7.4 — acabamento visual premium

- camada visual compartilhada `frontend/css/premium-polish.css`;
- tipografia reforçada e mais consistente em Cliente, Admin e Super Admin;
- botões, cards, formulários, tabelas e modais com hierarquia visual refinada;
- vitrine pública com cards mais consistentes e acabamento mais sofisticado;
- painéis administrativos com métricas, navegação e superfícies mais uniformes;
- área do cliente e acompanhamento com maior contraste e presença visual;
- nenhum endpoint, regra de negócio, modelo ou migration alterado;
- backend `24.7.4`; cache PWA `catalogo-digital-v24-7-4`.


## Hotfix 24.7.5 — publicação completa do frontend

- corrige o build do Render para publicar também subpastas de `frontend/js`, incluindo `frontend/js/shared/dom-utils.js`;
- restaura o carregamento correto dos scripts compartilhados usados por Cliente, Admin e Super Admin;
- atualiza o cache da PWA para evitar que o navegador mantenha assets antigos;
- sem migration; backend `24.7.5`.
