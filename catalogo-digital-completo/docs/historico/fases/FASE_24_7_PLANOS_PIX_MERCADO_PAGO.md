# Fase 24.7 — Planos dinâmicos + Pix imediato via Mercado Pago

## Objetivo

Transformar a cobrança das assinaturas do Catálogo Digital em um fluxo comercial real, mantendo totalmente separada a cobrança SaaS dos pagamentos que os clientes finais fazem às lojas.

## Planos iniciais

- Essencial — R$ 49,90/mês
- Profissional — R$ 89,90/mês — destaque inicial “Mais escolhido”
- Premium — R$ 149,90/mês

O plano Gratuito continua existindo apenas como contingência interna e não aparece para contratação pública.

Todos os preços, nomes, descrições, limites, recursos, período de teste, tolerância, destaque e disponibilidade comercial podem ser alterados no Super Admin. O preço anual começa vazio e pode ser habilitado depois.

## Proteção das condições comerciais

Ao ativar uma assinatura, o sistema grava um snapshot das condições contratadas (nome, preço, limites, recursos, teste e tolerância). Assim, editar um plano no Super Admin não muda silenciosamente as condições de lojas já assinantes. Uma troca de plano confirmada cria um novo snapshot.

## Pix imediato

Fluxo:

1. Admin escolhe um plano em “Meu plano”.
2. Pode aplicar cupom de assinatura.
3. Informa e-mail e CPF/CNPJ do pagador.
4. Backend cria o pagamento Pix no Mercado Pago usando chave de idempotência.
5. Admin recebe QR Code e Pix Copia e Cola.
6. A tela consulta o estado enquanto estiver aberta.
7. O webhook do Mercado Pago consulta o pagamento na API do provedor e valida referência, valor, moeda e meio de pagamento.
8. Somente após status aprovado a assinatura é ativada/alterada.

O Access Token e o segredo do webhook existem somente no backend e nunca devem ser colocados no frontend ou no Git.

## Variáveis de produção

Configurar no serviço Backend do Render:

- `MERCADO_PAGO_ACCESS_TOKEN`
- `MERCADO_PAGO_WEBHOOK_SECRET`
- `MERCADO_PAGO_WEBHOOK_URL=https://catalogo-digital-api.onrender.com/api/billing/webhooks/mercado-pago`

As duas credenciais devem ser configuradas juntas. Nunca registrar valores reais em arquivos `.env.example`, documentação, GitHub ou conversa.

## Webhook

Endpoint público:

`POST /api/billing/webhooks/mercado-pago`

A assinatura recebida em `x-signature` é validada com HMAC-SHA256 antes de qualquer atualização financeira. O evento é salvo de forma idempotente e o backend consulta o pagamento diretamente no Mercado Pago antes de ativar a assinatura.

## Visual

- vitrine pública em desktop com 3 produtos por linha;
- tablet com 2 produtos por linha;
- celular permanece com 1 produto por linha;
- tipografia reforçada em Cliente, Admin e Super Admin;
- cards de planos com selo e destaque comercial;
- checkout Pix com QR Code, Copia e Cola e confirmação automática.

## Migration

`019_dynamic_plans_pix`

A migration preserva IDs das assinaturas antigas, converte `BASICO` em `ESSENCIAL` e `EMPRESA` em `PREMIUM` quando aplicável e cria snapshots das condições existentes.
