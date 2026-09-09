# Fase 7 — Painel Administrativo Operacional

A Fase 7 transforma o painel visual da Fase 5/6 em uma área de gestão utilizável no dia a dia.

## Entregas

- CRUD visual de categorias.
- Criação, edição, ativação e desativação de produtos.
- Busca de produtos no painel.
- Ajuste manual de estoque e estoque mínimo.
- Criação, edição, ativação e desativação de serviços.
- Criação e edição de profissionais.
- Associação de profissionais aos serviços.
- Configuração semanal de horários por profissional.
- Gestão de status de pedidos e agendamentos.
- Resposta de orçamento com valor, mensagem e validade.
- Prévia visual das cores, logo e banner nas configurações da loja.
- Ações rápidas no dashboard.
- Melhorias responsivas no painel.

## Banco

A Fase 7 não cria tabelas novas. O head do Alembic continua `004_quotes`.

## Segurança

As operações continuam usando o usuário autenticado e o `store_id` resolvido no backend. O frontend não escolhe qual loja será alterada.
