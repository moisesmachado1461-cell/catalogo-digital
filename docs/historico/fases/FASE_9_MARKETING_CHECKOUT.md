# Fase 9 — Variações, adicionais, cupons, promoções e checkout

## Objetivo

Tornar o carrinho e o checkout capazes de representar produtos reais com variantes e adicionais, além de permitir campanhas promocionais por loja.

## Novas entidades

### coupons

Cupons pertencem a uma única loja e usam unicidade lógica `(store_id, code)`.

Principais campos: `code`, `discount_type`, `value`, `min_order_value`, `max_discount`, `usage_limit`, `usage_count`, `starts_at`, `ends_at`, `is_active`.

### coupon_usages

Registra o cupom e desconto aplicado a um pedido específico.

### promotions

Campanhas de desconto automático pertencentes à loja.

### promotion_items

Relaciona promoções aos produtos aos quais elas se aplicam.

## Checkout

Cada item do checkout pode enviar:

```json
{
  "product_id": 1,
  "variant_id": 4,
  "selected_option_item_ids": [9, 11],
  "quantity": 2
}
```

O backend nunca usa o preço enviado pelo navegador. Ele busca produto, variante, adicionais, promoção e cupom no banco e calcula o total no servidor.

## Regras de adicionais

O backend valida:

- se o adicional pertence ao produto;
- se está ativo;
- grupos obrigatórios;
- mínimo de escolhas;
- máximo de escolhas;
- IDs repetidos.

## Promoções

Promoções de produto são automáticas. Quando mais de uma promoção válida atingir o mesmo produto, o backend usa a que gerar o maior desconto.

## Cupons

Cupons são aplicados depois das promoções automáticas. O sistema valida loja, status, período de validade, pedido mínimo e limite de usos.

## Multi-tenant

Todos os registros de marketing possuem `store_id`. Rotas administrativas continuam usando o `store_id` do usuário autenticado, nunca um valor confiado ao frontend.
