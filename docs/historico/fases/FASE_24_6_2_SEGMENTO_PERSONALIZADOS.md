# Fase 24.6.2 — Estamparia, Personalizados e Brindes

Foi adicionado o segmento **Estamparia / Personalizados / Brindes**, usando o modelo operacional **Híbrido**.

## Por que Híbrido

Esse tipo de negócio costuma trabalhar em dois fluxos ao mesmo tempo:

1. **Venda direta de produtos prontos** — camisetas, moletons, chinelos, canecas, adesivos, kits e brindes.
2. **Trabalho personalizado/sob encomenda** — criação ou aplicação de estampas, personalização e pedidos que podem exigir orçamento antes da produção.

Criar um modelo totalmente separado seria desnecessário neste momento, porque o modelo Híbrido já combina catálogo e serviços. O segmento recebe capabilities próprias para habilitar o conjunto certo de recursos.

## Recursos padrão do segmento

- catálogo de produtos;
- carrinho e checkout;
- estoque;
- entrega/retirada conforme configuração da loja;
- pagamentos;
- serviços personalizados;
- solicitação de orçamento;
- cupons e promoções quando o plano permitir;
- variações e adicionais dos produtos já existentes no catálogo.

## Exemplos de uso

### Produtos prontos

- camisetas;
- moletons;
- canecas;
- chinelos;
- adesivos;
- brindes e kits.

### Serviços / sob encomenda

- estampa personalizada;
- personalização de camiseta/caneca;
- criação ou ajuste de arte;
- produção em quantidade;
- orçamento para encomendas especiais.

A loja pode usar os dois fluxos ao mesmo tempo, sem precisar escolher entre ser apenas e-commerce ou apenas prestadora de serviços.

## Banco de dados

A migration `018_personalizados_segment` adiciona a categoria em bancos já existentes. Novas instalações também recebem o segmento pelo `seed.py`.
