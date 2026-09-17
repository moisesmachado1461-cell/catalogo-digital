# Fase 10 — Agendamento profissional

Esta fase melhora a experiência de negócios de agenda (manicure, barbearia, salão, estética e similares) sem alterar o núcleo multi-tenant.

## Entregas

- fluxo público de agendamento em etapas;
- escolha visual de profissional e horário;
- uso automático do fuso horário do navegador;
- protocolo público único por agendamento;
- página pública para acompanhar o agendamento;
- cancelamento público quando o status e o horário permitem;
- bloqueios de agenda por profissional;
- bloqueios considerados no cálculo de disponibilidade;
- filtros de data e status na agenda administrativa;
- transições de status exibidas de acordo com a regra de negócio;
- vitrine de profissionais na página pública;
- limite de 180 dias para consulta/criação de horários.

## Migration

`006_booking_experience`

Adiciona `appointments.public_token` e a tabela `professional_blocks`.

## Segurança

- o protocolo público é aleatório e associado ao `slug` da loja;
- a consulta pública não permite navegar por IDs sequenciais;
- bloqueios administrativos usam o `store_id` derivado do JWT;
- um administrador não pode criar/excluir bloqueios de outra loja.
