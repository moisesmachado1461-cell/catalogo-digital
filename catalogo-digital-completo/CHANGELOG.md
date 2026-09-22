# Changelog — Catálogo Digital

Este arquivo resume os principais marcos. O histórico detalhado permanece em `docs/historico/`.

## 24.9.6 — Pix Marketplace sandbox

- cenário de teste Pix da Mercado Pago Orders API;
- sandbox usa dados predefinidos do provedor;
- produção mantém valor e dados reais;
- sem migration nova.

## 24.9.5 — OAuth Split Marketplace

- OAuth Marketplace corrigido e validado;
- APP ID usado conforme fluxo Split;
- PKCE S256 preservado;
- vendedor de teste conectado com sucesso.

## 24.9.0–24.9.4 — Pagamentos das lojas

- conexão de cada loja à própria conta Mercado Pago;
- tokens protegidos com criptografia;
- callback, webhook e fluxo PKCE;
- migration `020_store_marketplace_payments`.

## 24.8.x — Assistente / IA

- assistente contextual;
- IA backend;
- base central de conhecimento;
- respostas objetivas em PT-BR e proteção contra reasoning visível.

## 24.7.x — Planos e Pix SaaS

- planos dinâmicos;
- Pix Mercado Pago via Orders API;
- QR Code e Copia e Cola;
- reabertura de Pix pendente;
- refatoração frontend e acabamento premium.

## 24.4–24.6 — Auditoria, portal e experiência

- revisão integrada Cliente/Admin/Super Admin;
- release gate;
- portal do cliente e rastreamento;
- segmento Personalizados/Estamparia;
- carrinho separado e melhorias de UI/UX.

## Fases anteriores

Arquitetura SaaS, catálogo, serviços, pedidos, orçamentos, reservas, locações, segurança, LGPD, relatórios, PWA, Cloudinary, backup/restore, planos, cobrança e painéis premium. Consulte `docs/historico/`.
