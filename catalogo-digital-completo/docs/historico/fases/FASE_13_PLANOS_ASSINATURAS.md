# Fase 13 — Planos e Assinaturas

Esta fase transforma a estrutura multi-loja em uma base comercial de SaaS.

## Novidades

- tabela `plans`;
- tabela `subscriptions` com histórico por loja;
- planos Gratuito, Básico, Profissional e Empresa;
- preço mensal e anual editável;
- limites de produtos, serviços e profissionais;
- recursos por plano;
- painel "Meu plano" para o administrador da loja;
- gerenciamento de planos pelo Super Admin;
- troca manual de plano por loja;
- plano inicial ao criar nova loja;
- preparação para provedor de cobrança futuro (`provider`, IDs externos);
- bloqueio no backend quando a loja atinge limites de produtos, serviços ou profissionais;
- cupons e promoções podem ser condicionados ao plano.

## Valores iniciais

Os valores desta fase são uma configuração comercial inicial e podem ser alterados pelo Super Admin:

- Gratuito: R$ 0,00/mês;
- Básico: R$ 29,90/mês;
- Profissional: R$ 59,90/mês;
- Empresa: R$ 119,90/mês.

Nenhuma cobrança automática é realizada nesta fase. A alteração de assinatura ainda é administrativa/manual.

## Migration

```text
009_plans_subscriptions
```

## Segurança

O administrador da loja não escolhe seu próprio plano pela API administrativa. A mudança de plano fica restrita ao Super Admin.
