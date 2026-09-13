# Fase 24.8.0 — Assistente contextual

## Objetivo

Adicionar ajuda embutida e contextual ao Catálogo Digital sem alterar regras de negócio e sem depender de serviços pagos de IA.

## Funcionamento

O frontend carrega uma base de conhecimento versionada (`frontend/js/assistant-knowledge.js`) e o controlador visual (`frontend/js/assistant.js`). O assistente identifica automaticamente a área atual (loja, cliente, Admin ou Super Admin) e, quando possível, a seção ativa.

As respostas são selecionadas localmente por contexto e palavras-chave. Nenhuma senha, token ou dado privado é enviado para um serviço externo.

## Interface

- botão flutuante “Precisa de ajuda?”;
- painel de conversa responsivo;
- sugestões rápidas adaptadas à tela;
- respostas em passos quando necessário;
- integração visual com as cores da loja por meio de `--brand` e `--brand2`;
- suporte a `prefers-reduced-motion`.

## WhatsApp

Nesta fase, quando a página pública já expõe um link oficial de WhatsApp, o assistente pode oferecer “Continuar no WhatsApp”. A automação oficial do mesmo assistente dentro do WhatsApp Business fica para a próxima etapa e exigirá configuração da API oficial da Meta e um webhook dedicado.

## Segurança

O assistente desta fase é somente educativo. Ele não executa operações administrativas, não acessa senhas, não lê tokens e não altera dados do sistema.

## Banco de dados

Nenhuma migration.
