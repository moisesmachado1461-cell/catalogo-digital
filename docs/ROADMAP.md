# Catálogo Digital — Roadmap Completo, Continuidade, Ideias e Melhorias

**Documento mestre de continuidade do projeto**  
**Atualizado em:** 16/09/2026  
**Objetivo:** concentrar em um único arquivo o estado do projeto, decisões tomadas, melhorias planejadas, próximas fases, fluxo de trabalho, arquitetura, integrações, prioridades e estratégia futura.

> Este arquivo foi pensado para ser usado como referência em novos chats e também pode ser colocado no repositório como `docs/ROADMAP.md`.

---

# 1. VISÃO GERAL DO PROJETO

O **Catálogo Digital** é um SaaS multi-negócio e multi-loja, pensado para permitir que diferentes tipos de empresas usem a mesma plataforma com experiências adaptadas ao próprio segmento.

A plataforma deve atender negócios como:

- lojas de varejo;
- lojas de roupas;
- estamparias;
- personalizados e brindes;
- prestadores de serviços;
- barbearias e salões;
- profissionais com agenda;
- empresas que trabalham com orçamentos;
- pousadas e negócios com reservas;
- locadoras;
- negócios híbridos que vendem produtos e serviços.

A ideia não é vender um “site separado” para cada cliente. O modelo é **SaaS por assinatura**.

Cada lojista:

- cria a própria conta;
- possui a própria loja;
- possui seus próprios clientes;
- possui seus próprios pedidos;
- configura o próprio Mercado Pago;
- administra seu próprio catálogo;
- não compartilha senha com o dono da plataforma.

O proprietário do Catálogo Digital administra:

- infraestrutura;
- código;
- planos;
- assinaturas;
- Super Admin;
- atualizações;
- segurança;
- suporte;
- operação da plataforma.

---

# 2. AMBIENTE LOCAL E INFRAESTRUTURA

## Diretório principal no Windows

```text
C:\Users\SUNLIGHT\Downloads\catalogo-digital-arquitetura-v1-corrigido
```

## Ferramentas principais

- VS Code
- PowerShell
- Git / GitHub
- Python
- ambiente virtual em `backend\.venv`
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL em produção
- Render
- Cloudinary
- Mercado Pago
- PWA
- IA via API compatível com Chat Completions

## Comandos importantes

Ativar ambiente virtual quando necessário:

```powershell
backend\.venv\Scripts\Activate.ps1
```

Release gate principal:

```powershell
python backend\scripts\phase24_5_release_gate.py
```

Fluxo Git padrão:

```powershell
git add .
git commit -m "mensagem da fase"
git push
```

---

# 3. URLs IMPORTANTES

## Frontend público

```text
https://catalogo-digital-v3zs.onrender.com
```

## API / health

```text
https://catalogo-digital-api.onrender.com/api/health
```

Sempre confirmar a versão publicada através do `/api/health` após deploy.

---

# 4. FLUXO RÁPIDO OFICIAL

O projeto deve seguir o fluxo **FLUXORAPIDO**.

Evitar:

- muitos micro-patches;
- muitos deploys pequenos;
- várias fases minúsculas sem necessidade;
- mudanças aleatórias antes de capturar o erro real.

Preferir:

```text
1. Agrupar melhorias relacionadas
2. Gerar um ZIP consolidado
3. Copiar uma única vez
4. Rodar um único release gate
5. Fazer um commit
6. Fazer um push
7. Fazer um deploy
8. Testar apenas os fluxos afetados
```

Para erros de APIs externas:

```text
capturar erro exato
→ entender origem
→ corrigir
→ testar
```

Nunca continuar “chutando” configurações.

---

# 5. REGRA DE COMUNICAÇÃO PARA AS PRÓXIMAS FASES

Sempre explicar cada nova fase separando claramente:

## O que esta fase vai fazer

Explicar:

- quais mudanças serão feitas;
- qual benefício traz;
- o que será corrigido;
- o que será adicionado.

## O que você precisa fazer

Explicar:

- o que copiar;
- o que configurar;
- quais comandos executar;
- onde clicar;
- como testar.

Sempre fornecer uma **palavra-chave copiável** para avançar.

Exemplo:

```text
FASEOK
```

---

# 6. STATUS GERAL DO PRODUTO

Grande parte da estrutura já está implementada.

## Funcionalidades já presentes ou trabalhadas

- multi-lojas;
- multi-segmento;
- catálogo público;
- área Admin;
- Super Admin;
- área do cliente;
- login de clientes;
- produtos;
- categorias;
- estoque;
- carrinho;
- checkout;
- pedidos;
- acompanhamento de pedidos;
- serviços;
- agendamentos;
- reservas;
- locações;
- orçamentos;
- cupons;
- planos SaaS;
- planos editáveis;
- cobrança SaaS via PIX;
- PIX pendente reabrível;
- Cloudinary;
- PWA;
- backup;
- restore;
- segurança de rotas;
- CORS;
- autenticação;
- IA/chatbot;
- base de conhecimento;
- OAuth Mercado Pago Marketplace;
- separação SaaS x Marketplace;
- refatoração frontend;
- melhorias visuais;
- responsividade;
- segmento Estamparia / Personalizados / Brindes.

---

# 7. MELHORIAS VISUAIS JÁ DEFINIDAS

## Admin / Super Admin

- remover “Ações rápidas”;
- menu lateral no mobile semelhante ao desktop;
- sidebar recolhível;
- esconder itens quando recolhido;
- botão de recolher mais visível;
- tipografia mais robusta e profissional;
- botões mais interativos;
- feedbacks visuais;
- melhor uso das cores da loja;
- padronização visual de botões;
- cards mais profissionais;
- tabelas mais organizadas;
- formulários e modais mais refinados;
- nome “Catálogo Digital” personalizável em determinados contextos;
- logos e identificadores visuais mais claros.

## Loja pública

- carrinho separado dos cards;
- ícone de carrinho no topo;
- grid desktop 3×N;
- reduzir espaços em branco;
- login do cliente com tela própria e visual premium;
- identidade visual ligada às cores da loja;
- melhor tipografia;
- visual mais profissional;
- acompanhamento de pedidos.

---

# 8. SEGMENTO ESTAMPARIA / PERSONALIZADOS / BRINDES

Modelo híbrido planejado e já incorporado ao escopo.

Produtos possíveis:

- camisetas;
- moletons;
- canecas;
- chinelos;
- adesivos;
- kits;
- brindes;
- produtos prontos.

Também:

- personalização sob encomenda;
- orçamentos;
- pedidos;
- serviços;
- carrinho;
- checkout;
- estoque;
- cupons;
- pagamentos.

---

# 9. PAGAMENTOS SaaS — MERCADO PAGO / PIX

## Objetivo

Cobrar os planos do Catálogo Digital diretamente para o proprietário da plataforma.

Planos:

- Essencial — R$ 49,90/mês
- Profissional — R$ 89,90/mês
- Premium — R$ 149,90/mês

## Recursos já trabalhados

- planos editáveis pelo Super Admin;
- preço;
- nome;
- descrição;
- ciclo;
- trial;
- tolerância/grace;
- limites;
- recursos;
- destaque;
- ordem;
- ativo/inativo;
- snapshot de termos em assinaturas existentes.

## PIX SaaS

Já validado:

- geração de PIX;
- QR Code;
- Copia e Cola;
- modo sandbox;
- produção;
- PIX pendente;
- reabrir pagamento pendente;
- Orders API.

Falta apenas a validação definitiva de:

```text
pagamento real aprovado
→ webhook
→ assinatura ativada automaticamente
```

---

# 10. PAGAMENTOS DAS LOJAS — MARKETPLACE

Objetivo:

```text
cliente da loja paga
→ dinheiro vai para a conta Mercado Pago da própria loja
→ Catálogo Digital não recebe esse dinheiro
```

A arquitetura escolhida usa **OAuth Mercado Pago por loja**.

Cada lojista conecta a própria conta.

## Segurança

O sistema:

- não recebe senha do Mercado Pago;
- não recebe senha bancária;
- recebe autorização OAuth;
- armazena token de forma criptografada;
- separa as credenciais de cada loja;
- não deve permitir que uma loja veja pagamento de outra.

---

# 11. APLICAÇÕES MERCADO PAGO

Existem duas integrações separadas.

## 1. Catálogo Digital SaaS

Usada para:

```text
planos / assinaturas do SaaS
```

Não mexer nesta aplicação ao corrigir Marketplace.

## 2. Catálogo Digital Marketplace

Usada para:

```text
cada loja conectar sua própria conta Mercado Pago
```

---

# 12. VARIÁVEIS MERCADO PAGO — SaaS

Exemplos de nomes:

```text
MERCADO_PAGO_ACCESS_TOKEN
MERCADO_PAGO_WEBHOOK_SECRET
MERCADO_PAGO_WEBHOOK_URL
MERCADO_PAGO_TEST_MODE
```

Nunca colocar segredos em frontend.

Nunca enviar segredos em chats.

---

# 13. VARIÁVEIS MARKETPLACE

Principais:

```text
MERCADO_PAGO_MARKETPLACE_APP_ID
MERCADO_PAGO_MARKETPLACE_CLIENT_ID
MERCADO_PAGO_MARKETPLACE_CLIENT_SECRET
MERCADO_PAGO_MARKETPLACE_REDIRECT_URI
MERCADO_PAGO_MARKETPLACE_WEBHOOK_SECRET
STORE_PAYMENT_CREDENTIALS_KEY
STORE_PAYMENTS_TEST_MODE
FRONTEND_PUBLIC_URL
```

## Redirect URI

```text
https://catalogo-digital-api.onrender.com/api/payment-gateways/mercado-pago/callback
```

## Marketplace webhook

```text
https://catalogo-digital-api.onrender.com/api/payment-gateways/webhooks/mercado-pago
```

---

# 14. HISTÓRICO MARKETPLACE / OAUTH

O OAuth passou por várias correções até funcionar corretamente.

## Fase 24.9.5

Foi a fase que resolveu o OAuth Marketplace.

Resultado confirmado:

```text
OAUTHOK2495
```

Depois:

```text
VENDEDORTESTEOK
```

Isso confirma que:

- APP ID está correto;
- Client Secret está correto;
- PKCE funciona;
- callback funciona;
- vendedor de teste conseguiu conectar;
- OAuth Marketplace ficou operacional.

Não mexer novamente nessas credenciais sem necessidade.

---

# 15. FASE ATUAL — 24.9.6

## Objetivo

Testar o **PIX das lojas em sandbox**.

Fluxo desejado:

```text
Cliente faz pedido
→ escolhe PIX
→ sistema usa a conta Mercado Pago da loja
→ QR Code aparece
→ Copia e Cola aparece
→ pagamento fica pendente
→ Mercado Pago simula aprovação
→ webhook chega
→ pedido/pagamento atualizam automaticamente
```

## Pré-requisitos que já devem existir

- 24.9.5 publicada;
- OAuth Marketplace funcionando;
- conta vendedor de teste criada;
- conta comprador de teste criada;
- vendedor de teste conectado;
- `STORE_PAYMENTS_TEST_MODE=true`.

## Próximo teste

Aplicar / publicar a 24.9.6 e testar um pedido com PIX.

---

# 16. ROADMAP OFICIAL ATÉ O LANÇAMENTO

## 24.9.6 — PIX Loja Sandbox

Validar:

- criação da cobrança;
- QR Code;
- Copia e Cola;
- status pendente;
- webhook;
- aprovação simulada;
- atualização de pedido;
- isolamento por loja.

---

## 24.9.7 — PIX Loja Produção

Depois que sandbox estiver OK:

```text
STORE_PAYMENTS_TEST_MODE=false
```

Validar:

- conta real;
- PIX real;
- QR real;
- webhook real;
- pedido real;
- dinheiro indo para o lojista correto;
- isolamento multi-tenant.

---

# 17. FASE 24.10 — CADASTRO E ONBOARDING SEGURO DO LOJISTA

Esta fase é essencial antes do lançamento.

## Objetivo

Permitir que qualquer novo cliente crie e configure a própria conta sem depender do dono da plataforma.

Fluxo:

```text
Página inicial
→ Criar conta
→ Nome + e-mail + senha
→ Confirmar e-mail
→ Criar loja
→ Escolher segmento
→ Escolher plano
→ Configurar identidade visual
→ Cadastrar primeiro produto/serviço
→ Conectar Mercado Pago
→ Publicar loja
```

## Itens obrigatórios

### Cadastro autônomo

- cliente cria a própria conta;
- não precisa enviar senha ao suporte;
- senha armazenada somente como hash;
- proteção contra cadastros duplicados.

### E-mail verificado

Hoje um usuário poderia digitar um e-mail inexistente.

Isso deve ser corrigido.

Novo fluxo:

```text
usuário informa e-mail
→ sistema envia link ou código
→ usuário precisa abrir o e-mail
→ confirma
→ conta passa a “verificada”
```

Se o usuário não tiver acesso ao e-mail, não conclui a verificação.

Recursos:

- confirmação obrigatória;
- link/código;
- expiração;
- reenvio;
- limite de tentativas;
- proteção contra abuso;
- token de uso único;
- e-mail duplicado bloqueado;
- recuperação de senha apenas com e-mail verificado;
- status visível no Super Admin.

### Recuperação de senha

```text
Esqueci minha senha
→ recebe e-mail
→ cria nova senha
```

Sem o suporte saber a senha.

### Onboarding

Exemplo:

```text
1 de 6 — Configure sua loja
2 de 6 — Adicione sua logo
3 de 6 — Escolha suas cores
4 de 6 — Cadastre seu primeiro produto
5 de 6 — Conecte Mercado Pago
6 de 6 — Publique sua loja
```

Deve existir:

- progresso;
- autosave;
- retomada do ponto onde parou;
- instruções simples.

### Suporte temporário seguro

O lojista pode autorizar acesso temporário ao suporte.

Exemplo:

```text
Permitir suporte por 30 minutos
```

Registrar:

- quem acessou;
- quando;
- motivo;
- duração;
- encerramento.

Sem revelar senha.

---

# 18. FASE 24.11 — AUDITORIA FINAL / SEGURANÇA / REGRESSÃO

Depois de concluir pagamentos e onboarding.

Testar:

- cliente;
- Admin;
- Super Admin;
- login;
- cadastro;
- verificação de e-mail;
- recuperação de senha;
- produtos;
- categorias;
- estoque;
- pedidos;
- serviços;
- agendamentos;
- reservas;
- locações;
- orçamentos;
- cupons;
- planos;
- PIX SaaS;
- PIX lojas;
- Marketplace;
- chatbot;
- PWA;
- mobile;
- desktop.

Verificar também:

- erros JavaScript;
- erros Python;
- rotas quebradas;
- links quebrados;
- migrations;
- autenticação;
- autorização;
- isolamento multi-tenant;
- CORS;
- rate limit;
- uploads;
- Cloudinary;
- backups;
- restore;
- webhooks;
- logs;
- Sentry;
- segredos;
- criptografia.

---

# 19. FASE 24.12 — POLIMENTO FINAL

Fase de acabamento visual, experiência, documentação e preparação para versão 25.0.

---

# 20. MELHORIA — TEMA CLARO / ESCURO / AUTOMÁTICO

Adicionar em Configurações:

```text
Claro
Escuro
Automático
```

## Automático

Seguir preferência do aparelho / sistema operacional.

## Aplicar em

- página inicial;
- loja pública;
- Admin;
- Super Admin;
- área do cliente;
- login;
- cards;
- tabelas;
- formulários;
- modais;
- menus;
- pagamentos;
- chatbot.

## Requisitos

- preferência persistida;
- respeitar cores personalizadas da loja;
- não perder identidade visual;
- botão rápido no topo;
- opção detalhada em Configurações.

---

# 21. MELHORIA — CHATBOT ESPECIALISTA COMPLETO

O chatbot deve se tornar um **especialista total no Catálogo Digital**.

Ele deve conhecer:

- cada funcionalidade;
- cada tela;
- cada menu;
- cada área;
- cada plano;
- cada configuração;
- cada fluxo;
- pagamentos;
- Mercado Pago;
- produtos;
- estoque;
- pedidos;
- serviços;
- agendamentos;
- reservas;
- orçamentos;
- permissões;
- usuários;
- tema;
- onboarding;
- erros comuns;
- recuperação de senha;
- integrações.

## Requisitos

- PT-BR;
- respostas objetivas;
- contexto da tela atual;
- distinguir cliente / Admin / Super Admin / lojista;
- passo a passo;
- explicar erros;
- nunca inventar função inexistente;
- base central atualizada sempre que o sistema mudar.

Base existente:

```text
backend/app/assistant_knowledge.json
```

A melhoria definitiva deve acontecer perto do final, quando as funcionalidades já estiverem estáveis.

---

# 22. MELHORIA — EXPERIÊNCIA TIPO APP / PWA ADMIN

O Admin deve poder ser instalado como aplicativo.

## Objetivo

O lojista instala no celular/computador.

Depois aparece um ícone:

```text
Catálogo Digital
```

Ao tocar:

```text
se sessão ativa
→ abre direto no Admin

se sessão expirada
→ abre Login Admin
```

## Recursos desejados

- PWA instalável;
- ícone próprio;
- splash screen;
- experiência visual de aplicativo;
- navegação mobile;
- abertura rápida;
- atalho direto para Admin;
- sem necessidade de app nativo inicialmente.

---

# 23. MELHORIA — PÁGINA INICIAL / LANDING PAGE PREMIUM

A página inicial atual deve ficar muito mais comercial e apresentável.

Objetivos:

- parecer um SaaS profissional;
- transmitir confiança;
- explicar rapidamente o valor;
- mostrar segmentos;
- levar para demonstrações;
- levar para cadastro;
- converter visitantes em clientes.

## Conteúdo recomendado

Hero:

```text
Um sistema para vender, agendar, reservar e alugar.
```

Elementos:

- CTA forte;
- “Abrir demonstrações”;
- “Criar minha conta”;
- segurança;
- benefícios;
- segmentos;
- recursos;
- demonstrações reais;
- planos;
- perguntas frequentes;
- depoimentos futuros;
- comparação de planos;
- prova visual;
- seção “como funciona”.

Visual:

- premium;
- moderno;
- gradientes discretos;
- melhor hierarquia;
- tipografia robusta;
- cards refinados;
- animações sutis;
- sem excesso.

---

# 24. MELHORIAS PREMIUM PÓS-LANÇAMENTO

Não atrasar o lançamento por causa delas, salvo se alguma se tornar essencial.

## Domínio próprio por loja

Exemplo:

```text
www.bellamoda.com.br
```

Pode ser Premium.

---

## Analytics do lojista

Dashboard com:

- faturamento;
- pedidos;
- ticket médio;
- clientes;
- produtos mais vendidos;
- horários mais fortes;
- evolução por período;
- agendamentos;
- conversão.

---

## Mini CRM

Cada loja pode visualizar:

- clientes;
- histórico;
- total gasto;
- última compra;
- recorrência;
- observações;
- contatos autorizados.

---

## Funcionários e permissões

Exemplo:

- dono;
- gerente;
- atendente;
- funcionário.

Permissões diferentes.

Funcionário não precisa saber a senha do dono.

---

## Notificações profissionais

- novo pedido;
- pagamento aprovado;
- estoque baixo;
- novo agendamento;
- cancelamento;
- orçamento;
- assinatura;
- alerta interno;
- e-mail.

---

## Importação em massa

CSV / Excel.

Útil para lojas com muitos produtos.

---

## SEO e compartilhamento

- URLs amigáveis;
- título;
- descrição;
- imagem de compartilhamento;
- preview bonito;
- dados de produto;
- indexação adequada.

---

## Relatórios e exportação

- Excel;
- CSV;
- PDF.

Dados:

- pedidos;
- vendas;
- estoque;
- clientes;
- agendamentos;
- relatórios operacionais.

---

## Automações comerciais

Exemplos:

- estoque baixo;
- pedido parado;
- orçamento sem resposta;
- cliente inativo;
- carrinho abandonado;
- lembrete de agendamento.

---

## IA útil para o lojista

Além do chatbot de suporte:

- gerar descrição de produto;
- melhorar texto;
- sugerir título;
- analisar vendas;
- explicar métricas;
- responder perguntas sobre o próprio negócio.

Exemplo:

```text
“Qual produto mais vendeu este mês?”
```

---

## Personalização avançada

- banners;
- vitrines;
- seções reorganizáveis;
- produtos em destaque;
- templates;
- blocos visuais.

---

## Avaliações e depoimentos

Após pedido concluído:

- cliente avalia;
- loja escolhe exibição;
- prova social.

---

## Fidelidade

- pontos;
- cupons;
- cashback interno;
- recompensas;
- benefícios para clientes recorrentes.

---

## Central de cobrança SaaS

- plano atual;
- próxima cobrança;
- histórico;
- upgrade;
- downgrade;
- recursos do plano.

---

## Histórico de atividades

Exemplo:

```text
João alterou preço
Maria cancelou pedido
Gerente atualizou estoque
```

Importante para equipes.

---

# 25. DIFERENCIAÇÃO DOS PLANOS

Evitar que os planos sejam apenas:

```text
mesmo site + limite maior
```

Uma estrutura melhor:

## Essencial

Foco em:

- catálogo;
- pedidos;
- operação básica.

## Profissional

Foco em:

- relatórios;
- funcionários;
- gestão;
- automações.

## Premium

Foco em:

- IA;
- domínio próprio;
- personalização avançada;
- automações;
- recursos comerciais;
- suporte superior.

Isso aumenta o valor percebido.

---

# 26. PRINCÍPIO DE PRIORIZAÇÃO

Antes de adicionar uma melhoria, perguntar:

```text
Isso ajuda o lojista a:
1. vender mais?
2. economizar tempo?
3. administrar melhor?
4. parecer mais profissional?
```

Se não ajudar em pelo menos um desses pontos, provavelmente não deve atrasar o lançamento.

---

# 27. SEGURANÇA E PRIVACIDADE

O cliente não deve precisar entregar senha ao dono da plataforma.

## Senhas

- armazenar apenas hash;
- nunca exibir senha;
- nunca pedir senha por suporte;
- recuperação via e-mail.

## Mercado Pago

Usar OAuth.

O sistema não deve receber:

- senha Mercado Pago;
- senha bancária;
- 2FA;
- dados confidenciais desnecessários.

## Suporte

Usar:

- acesso temporário;
- autorização explícita;
- auditoria;
- sessão limitada.

---

# 28. LGPD / DOCUMENTOS LEGAIS

Antes do lançamento comercial, revisar/criar:

- Política de Privacidade;
- Termos de Uso;
- Política de dados;
- orientação sobre cookies quando aplicável;
- tratamento de dados;
- responsabilidades do lojista;
- responsabilidades da plataforma;
- exclusão/retorno/exportação de dados.

---

# 29. DOCUMENTAÇÃO FINAL

Ao final, limpar a raiz do projeto.

Hoje existem vários arquivos históricos como:

```text
INSTALAR_FASE_...
```

Eles não devem ficar bagunçando o projeto para sempre.

Organizar:

```text
README.md
CHANGELOG.md
docs/
docs/ROADMAP.md
docs/historico/
```

Mover documentação antiga para:

```text
docs/historico/
```

Não fazer essa limpeza antes da hora.

---

# 30. RELEASE FINAL

Meta:

```text
Catálogo Digital 25.0
```

Fluxo:

```text
1 ZIP final consolidado
1 release gate final
1 commit final
1 push
1 deploy
1 teste final de produção
```

Depois disso, considerar versão inicial comercial pronta.

---

# 31. ESTRATÉGIA DE VENDAS — APÓS 25.0

Depois de estabilizar o produto, criar uma estratégia **pesada, completa e profissional** de vendas.

Não apenas “postar nas redes”.

Cobrir:

- posicionamento;
- oferta;
- nichos;
- público-alvo;
- diferenciais;
- planos;
- preços;
- teste grátis;
- promoção de entrada;
- página de vendas;
- demonstrações;
- scripts;
- objeções;
- prospecção;
- conteúdo;
- aquisição;
- funil;
- onboarding;
- retenção;
- indicação;
- upsell;
- métricas;
- CAC;
- conversão;
- churn;
- MRR;
- metas;
- plano 30/60/90 dias.

## Princípio

Venda deve ser forte e estratégica, mas:

- profissional;
- sustentável;
- sem falsas promessas;
- baseada em valor real.

Palavra-chave futura:

```text
VENDASCATALOGOPESADA
```

---

# 32. COMO O SaaS DEVE SER VENDIDO

O cliente não compra o código-fonte.

Ele compra uma assinatura.

Fluxo:

```text
Conhece o Catálogo Digital
→ escolhe plano
→ cria conta
→ cria senha
→ confirma e-mail
→ configura loja
→ conecta Mercado Pago
→ começa a usar
```

O cliente controla:

- senha;
- loja;
- produtos;
- clientes;
- pedidos;
- conta Mercado Pago.

O dono da plataforma controla:

- SaaS;
- código;
- infraestrutura;
- Super Admin;
- planos;
- atualizações;
- suporte;
- segurança.

---

# 33. CHATBOT / IA — ESTADO ATUAL

Provider recomendado/configurado anteriormente:

Groq, via API compatível com Chat Completions.

Variáveis usadas:

```text
ASSISTANT_AI_ENABLED=true
ASSISTANT_AI_API_URL=https://api.groq.com/openai/v1/chat/completions
ASSISTANT_AI_API_KEY=<SEGREDO>
ASSISTANT_AI_MODEL=qwen/qwen3.6-27b
```

Nunca enviar a API key em chat.

O chatbot já recebeu ajustes para:

- PT-BR;
- respostas curtas;
- sem `<think>`;
- base central;
- fallback;
- contexto.

Ainda falta transformá-lo na versão “especialista total” na fase final.

---

# 34. WHATSAPP

Integração oficial com WhatsApp Business foi adiada.

Não deve bloquear o lançamento.

Pode ser feita depois.

Objetivo futuro:

- mesmo núcleo de conhecimento da IA;
- handoff para humano;
- integração oficial;
- atendimento automatizado.

---

# 35. PWA

Já existe base PWA no projeto.

A melhoria futura é transformar especialmente o Admin em experiência realmente “tipo app”:

- instalação;
- ícone;
- splash;
- abertura direta;
- sessão persistente;
- UX de aplicativo.

---

# 36. BACKUP / RESTORE

Já houve fases específicas de backup/recovery.

Na auditoria final:

- validar backup;
- validar restore;
- validar consistência;
- validar recuperação em caso de falha.

---

# 37. CLOUDINARY

Usado para:

- logos;
- banners;
- produtos;
- categorias;
- serviços;
- profissionais;
- ativos de locação.

Princípios:

- credenciais somente no servidor;
- validação;
- resize;
- WebP;
- URL persistente no banco.

---

# 38. PALAVRAS-CHAVE IMPORTANTES JÁ USADAS

Histórico de palavras-chave do projeto:

```text
PIXREAL
PIXERRO
PIXCHAVE
PIXDIAGNOSTICO
PIXDETALHE
FLUXORAPIDO
PIXPRODUCAO
PIXPENDENTE
PIXPENDENTEUI
PIXUIOK
CHATBOT
CHATBOTOK
IACATALOGO
IACONFIG
IAAUTO
IATESTE
IAOK
PAGAMENTOSLOJAS
MARKETPLACE
APPMARKETPLACE
WEBHOOKMARKETPLACE
MARKETPLACERENDER
OAUTHRETOMAR
OAUTHOK2495
PIXLOJATESTE
CONTASTESTEOK
VENDEDORTESTEOK
PIXTESTE2496
FASE2410ONBOARDING
EMAILVERIFICADO
TEMAESCURO
CHATBOTESPECIALISTA
MELHORIASPREMIUM
VENDASCATALOGOPESADA
FINALIZARCATALOGO
ONBOARDINGSEGURO
RETOMARCATALOGO
```

---

# 39. PALAVRA-CHAVE PARA RETOMAR EM NOVO CHAT

Se este chat acabar ou for necessário abrir outro:

```text
RETOMARCATALOGO
```

Idealmente, anexar este arquivo no novo chat.

Mensagem recomendada:

```text
RETOMARCATALOGO

Este arquivo contém o roadmap e o estado completo do projeto.
Quero continuar exatamente da fase atual, seguindo o FLUXORAPIDO e mantendo todas as decisões já registradas.
```

---

# 40. ESTADO EXATO PARA CONTINUIDADE AGORA

## Última confirmação importante

```text
OAUTHOK2495
VENDEDORTESTEOK
```

Marketplace OAuth já funciona.

## Fase atual

```text
24.9.6 — PIX Loja Sandbox
```

## Antes de avançar

Confirmar:

```text
Admin → Pagamentos → Mercado Pago conectado
```

## Próximo objetivo

Publicar/testar 24.9.6 e verificar:

```text
QR Code
Copia e Cola
status pendente
webhook
aprovação simulada
atualização do pedido
```

Depois:

```text
24.9.7 → produção
24.10 → cadastro + e-mail + onboarding
24.11 → auditoria
24.12 → polimento + tema + chatbot especialista + PWA + docs
25.0 → release oficial
→ estratégia de vendas
```

---

# 41. REGRAS DE SEGURANÇA PARA CONTINUIDADE

Nunca pedir ao usuário para enviar:

- Client Secret;
- Access Token;
- API Key;
- Webhook Secret;
- Fernet key;
- senha;
- código 2FA;
- credenciais privadas.

Quando precisar conferir configuração:

- pedir print com segredo oculto;
- pedir apenas nome da variável;
- pedir mensagem de erro;
- nunca o valor secreto.

---

# 42. META FINAL DO CATÁLOGO DIGITAL

A plataforma deve chegar ao lançamento sendo:

- bonita;
- profissional;
- rápida;
- segura;
- multi-loja;
- escalável;
- fácil de usar;
- fácil de vender;
- fácil de configurar;
- independente de suporte manual;
- com pagamentos por loja;
- com onboarding autônomo;
- com IA útil;
- com experiência mobile/app;
- com documentação;
- com planos que tenham valor real;
- preparada para crescer comercialmente.

---

# 43. RESUMO EXECUTIVO

Estado atual:

```text
Produto principal: muito avançado
OAuth Marketplace: funcionando
PIX SaaS: praticamente concluído
PIX loja sandbox: fase atual
Cadastro autônomo: planejado para 24.10
E-mail real/verificado: planejado para 24.10
Auditoria final: 24.11
Tema escuro: 24.12
Chatbot especialista: 24.12
Admin tipo app/PWA: 24.12
Landing page premium: polimento final
Limpeza/docs: 24.12
Release: 25.0
Estratégia pesada de vendas: após 25.0
```

---

# 44. FILOSOFIA FINAL DO PRODUTO

O Catálogo Digital não deve ser apenas:

```text
“um catálogo online”
```

Ele deve ser percebido como:

```text
uma plataforma completa para vender, atender, agendar, reservar, cobrar e administrar diferentes tipos de negócio.
```

E para o cliente pagante, a promessa prática deve ser:

```text
mais profissionalismo
+ menos trabalho manual
+ mais organização
+ mais possibilidades de venda
+ mais controle do negócio
```

---

**Fim do documento mestre.**
