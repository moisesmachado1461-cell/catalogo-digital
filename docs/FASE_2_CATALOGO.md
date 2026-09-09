# Fase 2 — Catálogo, Estoque e Pedidos

## Objetivo

Transformar a fundação multi-tenant em um catálogo comercial funcional no backend.

## Novas tabelas

- `categories`
- `products`
- `product_variants`
- `product_options`
- `product_option_items`
- `customers`
- `inventory`
- `orders`
- `order_items`

Todas as entidades de negócio são vinculadas à loja através de `store_id`.

## Regra multi-tenant

Rotas administrativas nunca recebem `store_id` como autoridade. O identificador da loja é obtido pelo backend a partir do administrador autenticado. Consultas por ID também incluem o filtro da loja.

## Teste rápido no Swagger

1. Execute `alembic upgrade head`.
2. Execute `python seed.py`.
3. Inicie `uvicorn app.main:app --reload`.
4. Abra `http://127.0.0.1:8000/docs`.
5. Teste `GET /api/public/stores/mercado-bom-preco/catalog`.
6. Clique em **Authorize** e entre com a conta demo.
7. Teste `GET /api/admin/products` e `GET /api/admin/inventory`.
8. Crie um pedido em `POST /api/public/stores/mercado-bom-preco/orders`.
9. Confira em `GET /api/admin/orders`.

### Corpo de exemplo para pedido

```json
{
  "customer": {
    "name": "Cliente Teste",
    "email": "cliente@example.com",
    "phone": "11999999999"
  },
  "items": [
    {
      "product_id": 1,
      "variant_id": null,
      "quantity": 2
    }
  ],
  "payment_method": "PIX",
  "fulfillment_method": "RETIRADA",
  "notes": "Pedido de teste"
}
```

O `product_id` deve existir no catálogo. Consulte o catálogo público ou a lista administrativa para descobrir o ID correto.

## Estoque

O preço e o total do pedido são calculados no backend. Se o produto controla estoque, o pedido só é criado quando existe quantidade suficiente. O pedido reduz o estoque e um cancelamento válido devolve a quantidade.

## Status permitidos

- `PENDENTE`
- `CONFIRMADO`
- `EM_PREPARACAO`
- `PRONTO`
- `SAIU_PARA_ENTREGA`
- `ENTREGUE`
- `CANCELADO`

As transições são verificadas no backend.
