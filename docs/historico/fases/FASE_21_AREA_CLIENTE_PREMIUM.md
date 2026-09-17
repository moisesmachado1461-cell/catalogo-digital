# Fase 21 — Área do Cliente Premium

A Fase 21 reformula a experiência pública das lojas sem alterar as regras de negócio existentes.

## Entregas

- cabeçalho com identidade da própria loja;
- hero premium responsivo com logo, banner, ações e destaques dinâmicos;
- navegação mais clara entre produtos, serviços, reservas, locações e contato;
- faixa de confiança/experiência;
- catálogo com busca, filtros, contador de resultados e cards refinados;
- carrinho com hierarquia visual melhor;
- serviços, profissionais, reservas e locações com cards mais consistentes;
- modais e formulários refinados;
- rodapé personalizado por loja;
- ajustes específicos para celular, tablet e desktop;
- suporte a `prefers-reduced-motion`;
- atualização do PWA/cache para carregar os novos estilos.

Nenhuma migration de banco é necessária.

## Validação mínima

1. `/api/health` retorna versão `21.0.0`.
2. Abrir uma loja com produtos e verificar busca, filtros e carrinho.
3. Abrir uma loja de serviços e verificar serviços/agendamento.
4. Testar no celular ou modo responsivo do navegador.
