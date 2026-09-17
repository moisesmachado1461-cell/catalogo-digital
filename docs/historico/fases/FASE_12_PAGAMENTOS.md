# Fase 12 — Pagamentos

A Fase 12 adiciona uma camada de pagamentos ao Catálogo Digital sem armazenar dados de cartão.

## Escopo desta fase

- PIX manual configurável por loja;
- dinheiro;
- cartão no atendimento/retirada/entrega;
- pagamento combinado por WhatsApp;
- registros de pagamento vinculados a:
  - pedidos;
  - agendamentos;
  - reservas;
  - locações;
- status de pagamento;
- confirmação manual pelo administrador;
- snapshot dos dados PIX usados no momento da cobrança;
- isolamento multi-tenant por `store_id`;
- estrutura com `provider` e `external_id` preparada para um gateway futuro.

## Importante

Esta fase **não envia transações para Mercado Pago nem para outro gateway externo**. O campo `provider` existe para preparar a arquitetura, mas o provedor ativo desta versão é `MANUAL`.

Não são armazenados número completo de cartão, CVV ou senha bancária.

## Migration

```text
008_payments
```

Novas tabelas:

```text
payment_settings
payments
```

## Configuração por loja

O administrador pode habilitar/desabilitar:

```text
PIX
Dinheiro
Cartão no atendimento/entrega
WhatsApp
```

Para PIX são armazenados:

```text
tipo da chave
chave PIX
nome do recebedor
cidade do recebedor
```

A chave configurada será exibida publicamente ao cliente quando ele escolher PIX. Se a chave for CPF ou CNPJ, o responsável pela loja deve estar ciente de que o dado ficará visível no fluxo de pagamento.

## Status

```text
PENDENTE
PAGO
RECUSADO
CANCELADO
```

Um pagamento `PAGO` não é apagado automaticamente se o pedido/agendamento for cancelado. Isso preserva o histórico e permite que um eventual estorno seja tratado em uma fase futura.

## Endpoints principais

Públicos:

```text
GET /api/public/stores/{slug}/payment-options
GET /api/public/stores/{slug}/payments/{token}
```

Administrativos:

```text
GET   /api/admin/payment-settings
PATCH /api/admin/payment-settings
GET   /api/admin/payments
PATCH /api/admin/payments/{payment_id}/status
```

## Frontend

O checkout, o agendamento, a reserva e a locação passam a usar as formas habilitadas pela própria loja.

Quando PIX é selecionado, o cliente recebe:

```text
valor
chave PIX
tipo de chave
nome do recebedor
instruções
```

O painel administrativo ganha a seção **Pagamentos** para configurar as formas aceitas e confirmar cobranças.

## Loja Ana Carolina

Depois de atualizar e executar o `seed.py`, lojas existentes com modelo `AGENDAMENTO` passam a receber a capability `payments`.

No painel da Ana Carolina:

```text
Pagamentos
→ Ativar PIX
→ Informar tipo da chave
→ Informar a chave real
→ Informar nome do recebedor
→ Salvar
```

Depois disso, PIX aparecerá como opção para clientes no fluxo de agendamento.

## Segurança

- cálculo de valores ocorre no backend;
- a forma escolhida é validada contra a configuração da loja;
- o administrador só vê pagamentos do próprio `store_id`;
- dados PIX são copiados para um snapshot no pagamento para preservar o histórico;
- nenhuma credencial de gateway é colocada no frontend;
- nenhum dado completo de cartão é armazenado.
