# Fase 24.8.1 — IA contextual do Catálogo Digital

## Objetivo

Evoluir o assistente 24.8.0 para uma IA com compreensão de linguagem natural, mantendo respostas objetivas e fundamentadas na base oficial do sistema.

## Arquitetura

1. O frontend identifica área e seção atual.
2. A busca local seleciona até 5 tópicos relevantes da base oficial.
3. O frontend envia pergunta, contexto e histórico curto para `/api/assistant/chat`.
4. O backend monta instruções restritas ao Catálogo Digital e chama o provedor configurado.
5. Se o provedor estiver indisponível ou não configurado, a resposta volta para a base local.

## Segurança e custo

- a chave da IA existe somente no backend/Render;
- o frontend nunca recebe a chave;
- o backend não envia senhas, tokens, Access Token do Mercado Pago ou secrets;
- perguntas têm tamanho limitado;
- o contexto é limitado a poucos trechos;
- histórico curto evita crescimento desnecessário de tokens;
- rate limit por cliente reduz abuso;
- respostas são limitadas em tamanho;
- a IA é instruída a não inventar funcionalidades.

## Variáveis de ambiente

```text
ASSISTANT_AI_ENABLED=true
ASSISTANT_AI_API_URL=https://SEU-PROVEDOR/v1/chat/completions
ASSISTANT_AI_API_KEY=SEGREDO
ASSISTANT_AI_MODEL=MODELO
ASSISTANT_AI_TIMEOUT_SECONDS=20
ASSISTANT_AI_MAX_TOKENS=320
ASSISTANT_AI_TEMPERATURE=0.2
ASSISTANT_AI_REQUESTS_PER_MINUTE=12
```

Use somente uma URL HTTPS em produção. `ASSISTANT_AI_API_KEY` nunca deve entrar no Git.

## Compatibilidade

A integração usa o formato comum de Chat Completions (`model`, `messages`, `temperature`, `max_tokens`). Assim, o projeto não fica preso a um único fornecedor.

## Migration

Nenhuma.
