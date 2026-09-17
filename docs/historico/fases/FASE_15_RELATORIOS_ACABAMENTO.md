# Fase 15 — Relatórios, Dashboard Avançado e Exportações

A Fase 15 transforma dados operacionais já existentes em informação útil para o administrador da loja.

## Entregas

- dashboard com resumo de desempenho dos últimos 30 dias;
- área **Relatórios** habilitada para planos com `features.reports = true`;
- períodos de 7, 30, 90 e 365 dias;
- indicadores de pedidos, receita, ticket médio, clientes, agendamentos, orçamentos, reservas, locações, pagamentos e estoque baixo;
- evolução diária em gráfico sem bibliotecas externas;
- ranking de produtos vendidos e serviços mais agendados;
- exportação CSV de pedidos, clientes, agendamentos, pagamentos, orçamentos, reservas e locações;
- exportações protegidas por autenticação, `store_id` e recurso do plano.

## Endpoints

```text
GET /api/admin/reports/overview
GET /api/admin/reports/timeseries
GET /api/admin/reports/top-items
GET /api/admin/reports/export.csv
```

Parâmetros de período aceitos: `7`, `30`, `90` e `365`.

## Segurança multi-tenant

O frontend não envia `store_id`. O backend deriva a loja do usuário autenticado e filtra todas as consultas por esse `store_id`.

A exportação CSV segue a mesma regra e exige token JWT válido.

## Banco de dados

Esta fase não cria novas tabelas. Portanto, a migration atual permanece:

```text
010_security_lgpd (head)
```

## Planos

Relatórios são exibidos apenas quando o plano efetivo da loja possui:

```json
{"reports": true}
```

Nas configurações padrão, os planos Profissional e Empresa possuem esse recurso.
