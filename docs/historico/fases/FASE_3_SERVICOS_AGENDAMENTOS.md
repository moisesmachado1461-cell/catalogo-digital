# Fase 3 — Serviços, Profissionais e Agendamentos

## Objetivo

Validar que o Catálogo Digital atende negócios baseados em serviços e agenda, sem duplicar a plataforma usada por lojas de varejo.

## Novas tabelas

- `services`
- `professionals`
- `professional_services`
- `professional_hours`
- `appointments`

Todas as tabelas de negócio possuem isolamento por `store_id` quando aplicável.

## Regras principais

1. A loja precisa ter `services=true` para expor e administrar serviços.
2. A loja precisa ter `appointments=true` para profissionais, disponibilidade e agendamentos.
3. Serviço, profissional, cliente e agendamento devem pertencer à mesma loja.
4. O profissional precisa estar explicitamente associado ao serviço.
5. O início do agendamento deve incluir fuso horário, por exemplo `2030-01-07T10:00:00-03:00`.
6. O backend calcula `ends_at` usando `duration_minutes` do serviço.
7. O horário precisa estar dentro da jornada do profissional.
8. Agendamentos `PENDENTE` ou `CONFIRMADO` bloqueiam sobreposição.
9. O backend recusa agendamentos no passado.
10. Um administrador nunca escolhe `store_id`; ele vem do JWT.

## Status

- `PENDENTE`
- `CONFIRMADO`
- `CONCLUIDO`
- `CANCELADO`
- `NAO_COMPARECEU`

Transições:

- PENDENTE → CONFIRMADO | CANCELADO
- CONFIRMADO → CONCLUIDO | CANCELADO | NAO_COMPARECEU
- Estados finais não podem ser alterados nesta fase.

## Endpoints públicos

- `GET /api/public/stores/{slug}/services`
- `GET /api/public/stores/{slug}/availability`
- `POST /api/public/stores/{slug}/appointments`

A disponibilidade recebe:

- `service_id`
- `professional_id`
- `date` no formato `AAAA-MM-DD`
- `utc_offset_minutes` (Brasil/Brasília normalmente `-180`)
- `slot_interval_minutes` (padrão `15`)

## Endpoints administrativos

Serviços:

- `GET /api/admin/services`
- `POST /api/admin/services`
- `PUT /api/admin/services/{service_id}`
- `DELETE /api/admin/services/{service_id}`

Profissionais:

- `GET /api/admin/professionals`
- `POST /api/admin/professionals`
- `PUT /api/admin/professionals/{professional_id}`
- `DELETE /api/admin/professionals/{professional_id}`
- `PUT /api/admin/professionals/{professional_id}/services`
- `PUT /api/admin/professionals/{professional_id}/hours`

Agendamentos:

- `GET /api/admin/appointments`
- `GET /api/admin/appointments/{appointment_id}`
- `PATCH /api/admin/appointments/{appointment_id}/status`

## Loja demonstrativa

`Barbearia Central Demo`

- slug: `barbearia-central-demo`
- admin de desenvolvimento: `admin@barbeariacentral.com`
- senha de desenvolvimento: `Admin@24680`
- 4 serviços
- 2 profissionais
- horários segunda a sábado, 09:00–18:00

As credenciais acima são somente para ambiente local/demonstração e devem ser substituídas em produção.

## Atualização a partir da Fase 2

Preserve:

- `backend/.venv`
- `backend/.env`
- `backend/catalogo.db`

Depois de copiar os arquivos da Fase 3 sobre o projeto existente, execute dentro de `backend`:

```powershell
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

A migration nova é `003_services_appointments`.
