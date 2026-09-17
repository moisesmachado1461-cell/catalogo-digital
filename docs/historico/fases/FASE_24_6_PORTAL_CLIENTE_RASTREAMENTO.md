# Fase 24.6 — Portal do Cliente e Acompanhamento

## Objetivo

Separar claramente os três públicos do SaaS:

1. Super Admin — administra a plataforma.
2. Admin da loja — administra uma empresa/tenant.
3. Cliente final — acompanha apenas os próprios pedidos e agendamentos daquela loja.

## Portal do cliente

A nova página `frontend/cliente.html` usa autenticação própria por loja. A conta é armazenada em `customer_accounts` e vinculada a um registro `customers` do mesmo `store_id`.

A sessão do cliente usa JWT com subject `customer:<account_id>`, portanto não é aceita nas rotas do Admin ou Super Admin.

## Vinculação segura de histórico

Quando já existe um pedido/agendamento antes da criação da conta, o cadastro pode receber o token público desse acompanhamento. O sistema só vincula o histórico se o token pertence à mesma loja e ao mesmo cliente. Quando o registro ainda não possui e-mail, a posse do token permite definir o e-mail durante o cadastro.

O cadastro sem token não assume automaticamente históricos existentes para um e-mail, evitando que uma pessoa reivindique pedidos antigos apenas informando um endereço de e-mail.

## Acompanhamento sem login

Pedidos recebem `public_token` aleatório, não sequencial, e podem ser consultados por:

`GET /api/public/stores/{slug}/orders/{public_token}`

Agendamentos mantêm o token público já existente. A página `frontend/acompanhar.html` apresenta os dois fluxos.

A resposta pública não expõe e-mail ou telefone do cliente.

## Status apresentados

Pedido com entrega:

`Recebido → Confirmado → Em preparação → Pronto → Saiu para entrega → Entregue`

Pedido com retirada:

`Recebido → Confirmado → Em preparação → Pronto para retirada → Retirado`

Agendamento:

`Solicitado → Confirmado → Concluído`

Cancelamentos e não comparecimento aparecem como estados terminais especiais.

## Interface

A mesma fase conclui os refinamentos solicitados antes do lançamento:

- ícones semânticos maiores e mais legíveis nos cards Admin/Super Admin;
- ações de produto alinhadas em grade, com ícones e cores derivadas da identidade da loja;
- sidebar recolhível no desktop/notebook e drawer lateral no celular;
- acesso `Minha conta` na loja pública;
- modal de sucesso do pedido com botões de acompanhamento e criação de conta.

## Banco de dados

Migration: `017_customer_portal`

- cria `customer_accounts`;
- adiciona `orders.public_token`;
- gera token também para pedidos já existentes durante a migration.

Backend: `24.6.0`.
