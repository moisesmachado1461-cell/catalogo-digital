# Fase 24.8.2 — Base de conhecimento automática da IA

## Objetivo

Manter o Assistente do Catálogo Digital atualizado sem treinar novamente o modelo de IA e sem duplicar regras de negócio no prompt.

## Fonte oficial

A fonte canônica é:

`backend/app/assistant_knowledge.json`

Cada tópico informa as áreas e seções em que é relevante, título, palavras-chave, resposta oficial e passos opcionais.

## Como funciona

1. O backend carrega a base oficial.
2. Para cada pergunta, ranqueia os tópicos pelo contexto da tela e pelo texto da dúvida.
3. Envia somente os tópicos relevantes ao provedor de IA.
4. Se a IA estiver indisponível, usa o melhor tópico oficial como fallback.
5. O arquivo é recarregado automaticamente quando muda.

## Atualizações futuras

Sempre que uma fase adicionar ou alterar uma funcionalidade, a mesma alteração deve atualizar a entrada correspondente na base oficial. Não é necessário treinar o modelo nem alterar a chave da API.

O fallback do frontend pode ser sincronizado com:

```powershell
python backend\scripts\sync_assistant_knowledge.py
```

## Segurança

O backend ignora o conhecimento enviado pelo navegador como fonte confiável da IA. Isso reduz o risco de um cliente adulterar os trechos enviados e tentar injetar instruções no contexto do modelo.

Nenhuma senha, token, chave de API ou segredo faz parte da base de conhecimento.

## Verificação

Com o backend online:

`GET /api/assistant/knowledge/status`

deve retornar a versão da base e a quantidade de tópicos carregados.
