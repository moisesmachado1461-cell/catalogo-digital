# Fase 19.2 — Motor de cobrança e ciclo de assinaturas

A Fase 19.2 implementa o ciclo interno de cobrança do SaaS sem depender ainda
de uma conta do Mercado Pago ou de outro provedor.

## O que está funcional

- geração idempotente de fatura de renovação;
- fatura pendente para troca de plano sem alterar o plano atual antes do pagamento;
- confirmação manual de pagamento;
- falha de pagamento e status `PAST_DUE`;
- período de tolerância configurável;
- expiração depois da tolerância;
- cancelamento imediato ou ao fim do período;
- renovação de plano gratuito sem cobrança;
- histórico de tentativas de pagamento;
- auditoria das ações do Super Admin;
- processamento diário repetível via API ou script.

Nenhuma cobrança bancária é simulada. Enquanto não houver gateway real, o
provedor `MANUAL` representa somente o controle administrativo de recebimentos.

## Novos dados de fatura

A migration `012_billing_engine` adiciona em `subscription_invoices`:

- `plan_id`;
- `invoice_type` (`RENEWAL` ou `PLAN_CHANGE`);
- `billing_cycle`;
- `period_start` e `period_end`;
- `attempt_count` e `last_attempt_at`.

## Política padrão

- fatura de renovação: criada até 7 dias antes do vencimento;
- tolerância após vencimento: 5 dias;
- moeda: BRL.

Podem ser ajustadas por ambiente:

```text
BILLING_DEFAULT_CURRENCY=BRL
BILLING_INVOICE_LEAD_DAYS=7
BILLING_GRACE_DAYS=5
```

## API de Super Admin

- `GET /api/super-admin/billing/invoices`
- `POST /api/super-admin/billing/subscriptions/{id}/renewal-invoice`
- `POST /api/super-admin/billing/subscriptions/{id}/change-plan`
- `PATCH /api/super-admin/billing/invoices/{id}/status`
- `POST /api/super-admin/billing/subscriptions/{id}/cancel`
- `POST /api/super-admin/billing/process-due`

A área da loja continua podendo consultar:

- `GET /api/admin/billing/overview`

## Regra importante para troca de plano

Uma troca paga não muda o plano imediatamente quando a fatura é criada. O
plano atual permanece intacto enquanto a fatura estiver pendente. O novo plano
entra em vigor somente quando a fatura de troca recebe `PAID`.

## Período de tolerância

Uma assinatura `PAST_DUE` continua reconhecida como efetiva durante o número de
dias configurado em `BILLING_GRACE_DAYS`. Depois disso, o motor marca como
`EXPIRED` e o sistema volta ao plano gratuito de fallback.

## Processamento recorrente

O comando abaixo executa uma passagem segura e idempotente:

```powershell
cd backend
python scripts/process_subscription_billing.py
```

Mais adiante esse mesmo comando pode ser ligado a um agendador de produção.
Nesta fase não é necessário configurar job externo para concluir a instalação.

## Próximo passo

Fase 19.3: tela profissional **Meu plano e cobrança** para o administrador e
controles financeiros correspondentes no Super Admin. A integração do Mercado
Pago fica desacoplada e pode ser adicionada depois, quando houver uma conta
elegível disponível.
