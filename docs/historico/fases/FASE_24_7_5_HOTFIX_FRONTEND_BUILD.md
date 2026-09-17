# Fase 24.7.5 — Hotfix do build do frontend

Corrige o deploy do frontend no Render após a refatoração que introduziu `frontend/js/shared/dom-utils.js`.

O `render-build.sh` antigo copiava apenas `js/*.js`, ignorando subpastas. Com isso, `js/shared/dom-utils.js` não chegava ao diretório `dist`, causando falha de JavaScript e impedindo login e carregamento das áreas que dependem de `CatalogoUtils`.

A correção passa a copiar a árvore `js/` recursivamente e renova o cache da PWA.

Nenhuma regra de negócio, banco, autenticação ou integração de pagamento foi alterada.
