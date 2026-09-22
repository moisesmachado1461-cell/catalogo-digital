# Fase 23.4 — Cupons avançados e cupons de planos

A Fase 23.4 separa formalmente duas categorias de desconto da plataforma.

## 1. Cupons comerciais da loja

O administrador da loja continua criando promoções para os próprios clientes,
mas agora cada cupom pode ser aplicado:

- ao pedido inteiro; ou
- somente a produtos selecionados.

Na listagem de produtos do Admin existe um atalho **Cupom**, que abre o editor
já preparado para vincular aquele produto. O editor de cupons também permite
marcar vários produtos.

A regra é validada no backend. Em cupom de produtos, somente o subtotal dos
itens elegíveis participa do cálculo do desconto. O mínimo do pedido, quando
configurado, continua considerando o carrinho completo.

A associação é armazenada em `coupon_products`.

## 2. Cupons dos planos do Catálogo Digital

Cupons de assinatura pertencem ao SaaS e são administrados exclusivamente pelo
Super Admin. Eles não reutilizam a tabela de cupons das lojas.

O Super Admin pode definir:

- código e descrição;
- percentual ou valor fixo;
- desconto máximo;
- validade;
- limite de usos;
- todos os planos ou planos específicos;
- primeira fatura apenas (`FIRST_INVOICE`) ou desconto recorrente (`RECURRING`).

O Admin da loja acessa **Meu plano**, escolhe um plano disponível, seleciona o
ciclo mensal/anual e informa um código. O backend calcula e devolve o subtotal,
o desconto e o total antes da confirmação.

Enquanto o gateway automático real não estiver conectado, a solicitação gera
uma fatura `PENDING`. A troca de plano só é efetivada quando o Super Admin
confirma a fatura como paga. Isso evita conceder recursos de plano sem pagamento.

Cupons recorrentes permanecem associados à assinatura e podem ser aplicados às
renovações enquanto continuarem válidos. O uso é contabilizado quando a fatura
é efetivamente marcada como paga, não apenas na simulação.

## Segurança e consistência

- validação de cupons é sempre feita no backend;
- cupons de loja respeitam `store_id`;
- cupons de assinatura são globais do SaaS e controlados pelo Super Admin;
- o Admin não pode editar cupons de assinatura;
- o sistema impede solicitar novamente o mesmo plano no mesmo ciclo apenas para
  reiniciar período ou reaplicar desconto;
- o valor original, o desconto e o código usado ficam registrados na fatura.

## Banco de dados

Migration: `015_advanced_coupons`.

Principais estruturas novas:

- `coupon_products`;
- `billing_coupons`;
- `billing_coupon_plans`;
- `billing_coupon_usages`;
- campos de subtotal/desconto/cupom em `subscription_invoices`;
- cupom recorrente opcional em `subscriptions`.

Versão do backend: `23.4.0`.
