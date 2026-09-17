# Fase 24.7.3 — Refatoração segura e limpeza de código

## Objetivo

Melhorar legibilidade, organização e manutenção sem alterar comportamento, regras de negócio, endpoints, banco ou funcionalidades.

## Alterações

- novo `frontend/js/shared/dom-utils.js` para consultas DOM, iniciais e helpers de formulário;
- remoção de helpers duplicados em Admin, Super Admin, loja pública, portal do cliente e acompanhamento;
- `frontend/js/api.js` refatorado em funções menores e constantes nomeadas;
- `renderSubscription()` dividido em componentes de renderização focados;
- `acompanhamento.js` reformatado, com constantes de status/etapas e funções menores;
- imports Python não utilizados removidos;
- carregamento de scripts HTML padronizado;
- `.editorconfig` adicionado para padronizar indentação, fim de linha e whitespace;
- PWA atualizado para incluir o novo utilitário compartilhado.

## Garantias

- nenhuma migration nova;
- nenhuma biblioteca nova;
- nenhuma feature nova;
- nenhum endpoint alterado;
- nenhum formato de payload alterado;
- nenhuma regra de cobrança, autenticação ou multi-tenant alterada.

## Validação

- `node --check` em todos os arquivos JavaScript;
- `python -m compileall` no backend e scripts;
- auditoria estrutural do projeto;
- revisão integrada Cliente + Admin + Super Admin;
- release gate completo deve ser executado na `.venv` do projeto antes do commit/push.
