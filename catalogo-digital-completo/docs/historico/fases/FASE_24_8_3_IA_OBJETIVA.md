# Fase 24.8.3 — IA objetiva em português

Ajuste de apresentação do assistente para impedir exposição de reasoning interno ao usuário final.

## Regras
- português do Brasil;
- somente resposta final;
- no máximo 4 passos curtos;
- sem `<think>`;
- resposta curta para atendimento rápido.

Para Groq + Qwen, o backend envia `reasoning_effort=none` e `reasoning_format=hidden`. Há sanitização adicional no backend caso o provedor ignore a configuração.
