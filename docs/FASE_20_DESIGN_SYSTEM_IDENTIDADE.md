# Fase 20 — Design System e identidade visual oficial

A Fase 20 cria a fundação visual compartilhada do Catálogo Digital antes das reformas específicas de Cliente, Admin e Super Admin.

## Objetivo

Evitar três interfaces desconectadas e evitar retrabalho. A partir desta fase, novas telas devem reutilizar os mesmos tokens e componentes visuais.

## O que foi criado

- `frontend/css/design-system.css`
  - cores e superfícies;
  - sombras e elevação;
  - raios de borda;
  - estados de foco;
  - botões e campos;
  - cards e painéis;
  - tabelas e status;
  - sidebar administrativa;
  - modais;
  - base responsiva;
  - skeleton loading;
  - animações com respeito a `prefers-reduced-motion`.
- `frontend/js/ui-system.js`
  - inicialização da camada visual v20;
  - efeito de topbar ao rolar;
  - microanimações discretas;
  - componente global de toast para uso futuro;
  - aviso de perda/retorno de conexão.
- Todas as páginas HTML carregam o Design System.
- Service Worker atualizado para cachear os novos assets.
- PWA com paleta atualizada.
- Backend identificado como versão `20.0.0`.

## Regra para marcas e meios de pagamento

Marcas que possuem identidade própria devem usar seus logotipos/ativos oficiais quando forem implementadas. Não inventar um logotipo alternativo para Mercado Pago, PicPay, Nubank, Visa, Mastercard e equivalentes.

## Limites desta fase

Esta fase NÃO é a reforma completa das telas. Ela estabelece a fundação.

Próximas etapas:

- Fase 21: área do cliente / loja pública premium;
- Fase 22: painel Admin premium;
- Fase 23: painel Super Admin premium.
