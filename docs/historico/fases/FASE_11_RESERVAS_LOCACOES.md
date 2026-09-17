# Fase 11 — Reservas e Locações

Esta fase amplia o Catálogo Digital para negócios cujo fluxo principal é reservar um recurso por período ou alugar um item.

## Reservas

Novas entidades:

- `resources`: quartos, suítes, salões, salas, espaços ou outros recursos reserváveis;
- `reservations`: cliente, recurso, início, fim, quantidade de pessoas, preço e status.

O backend bloqueia períodos sobrepostos para o mesmo recurso enquanto a reserva estiver `PENDENTE` ou `CONFIRMADA`.

Status: `PENDENTE`, `CONFIRMADA`, `CONCLUIDA`, `CANCELADA`.

## Locações

Novas entidades:

- `rental_items`: item, SKU, diária, caução e quantidade total;
- `rental_reservations`: período, quantidade, diária congelada no momento da locação, caução e total.

A disponibilidade considera todas as locações ativas que se sobrepõem ao período pedido. O backend nunca confia em uma quantidade calculada pelo frontend.

Status: `PENDENTE`, `CONFIRMADA`, `RETIRADA`, `DEVOLVIDA`, `CANCELADA`.

## Multi-tenant

Todos os registros possuem `store_id`. Rotas administrativas obtêm a loja do usuário autenticado. Recursos e itens de outra loja não podem ser vinculados a reservas ou locações.

## Migration

`007_reservations_rentals`

## Demonstrações

- Pousada Serena Demo — modelo `RESERVA`;
- Aluga Fácil Demo — modelo `LOCACAO`.

A API passa para a versão `11.0.0`.
