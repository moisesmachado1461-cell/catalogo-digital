# Fase 23.3 — Lojas e Cupons

Atualização cumulativa a partir da Fase 23.1. Inclui a restauração da edição completa de lojas da Fase 23.2 e amplia o módulo de cupons.

## Super Admin
- editar dados completos da loja;
- abrir a loja pública;
- gerenciar os cupons de cada loja;
- criar e editar código, tipo, valor, pedido mínimo, desconto máximo, limite de usos, validade, status e visibilidade pública;
- auditoria das alterações de cupons feitas pelo Super Admin.

## Admin da loja
- edição de cupons preservada e melhorada;
- validade inicial/final;
- ativar/desativar;
- marcar “Exibir este cupom no site da loja”;
- visualizar status, uso e visibilidade pública.

## Loja pública
- endpoint público lista apenas cupons ativos, públicos, dentro da validade e ainda disponíveis;
- nova área “Cupons”;
- cliente pode copiar ou selecionar um cupom;
- cupom selecionado é levado para o checkout e validado novamente no servidor.

## Segurança
Cupons privados não são expostos publicamente. A validação real continua no backend, incluindo loja, status, período, limite de usos e pedido mínimo.

## Banco
Migration `014_public_coupons`: adiciona `coupons.is_public` com padrão seguro `false`.

Backend: `23.3.0`.
