# Fase 6 — Super Admin e cadastro de lojas

Esta fase transforma a base multi-tenant em uma operação SaaS administrável.

## Entregas

- Conta de Super Admin sem `store_id`.
- Autorização exclusiva por role `SUPER_ADMINISTRADOR`.
- Dashboard global com lojas, pedidos, clientes, produtos, agendamentos, orçamentos e valor bruto de pedidos.
- Lista de lojas com administrador e métricas por tenant.
- Criação de loja + administrador em uma única transação.
- Modelo de negócio derivado da categoria escolhida.
- Capabilities iniciais derivadas do modelo/categoria, sem confiar no frontend.
- Slug único gerado pelo backend.
- Ativação/desativação lógica de lojas.
- Tela visual `super-admin.html`.

## Segurança

O endpoint de criação não aceita `store_id` para o administrador. O backend cria a loja, obtém o ID real e então vincula o usuário. A categoria escolhida determina o modelo de negócio e as capabilities iniciais.

## Credencial local de demonstração

- `superadmin@catalogodigital.dev`
- `SuperAdmin@2026`

Troque a credencial antes de qualquer publicação real.

## Banco

A Fase 6 reutiliza as tabelas `stores` e `users`; portanto não exige migration 005. A migration atual continua `004_quotes (head)`.
