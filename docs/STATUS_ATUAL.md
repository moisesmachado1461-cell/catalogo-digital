# Catálogo Digital — Status atual

**Código atual:** `24.9.6`  
**Último marco confirmado:** OAuth Marketplace funcionando (`OAUTHOK2495`) e vendedor de teste conectado (`VENDEDORTESTEOK`).  
**Fase em validação:** Pix das lojas em sandbox.

## Estado confirmado

- SaaS multi-loja / multi-segmento operacional.
- Cliente, Admin e Super Admin separados e responsivos.
- Catálogo, produtos, categorias, estoque, carrinho e checkout.
- Serviços, agendamentos, orçamentos, reservas e locações.
- Cupons, planos e assinaturas SaaS.
- Pix SaaS com QR Code, Copia e Cola e reabertura de cobrança pendente.
- Cloudinary, PWA, backup/restore e observabilidade.
- Assistente contextual com base de conhecimento e IA em PT-BR.
- Mercado Pago Marketplace via OAuth/PKCE por loja.
- Tokens de vendedores protegidos no backend.
- Migration atual: `020_store_marketplace_payments`.

## Fase 24.9.6 — Pix Marketplace sandbox

Objetivo do código 24.9.6:

```text
Cliente faz pedido
→ escolhe Pix Mercado Pago
→ cobrança usa a conta do vendedor conectado
→ QR Code + Copia e Cola
→ status pendente
→ Mercado Pago simula aprovação
→ webhook
→ pagamento/pedido atualizados
```

Com `STORE_PAYMENTS_TEST_MODE=true`, o provedor recebe o cenário oficial de teste Pix da Orders API. Produção continua usando os dados reais.

### Próximo teste

1. Executar `python backend\scripts\phase24_5_release_gate.py`.
2. Publicar a 24.9.6 se o gate estiver aprovado.
3. Confirmar `/api/health` em `24.9.6`.
4. Criar um pedido na loja pública e escolher Pix Mercado Pago.
5. Confirmar QR Code, Copia e Cola, webhook e atualização automática.

## Próximas fases

- `24.9.7` — Pix das lojas em produção.
- `24.10` — cadastro autônomo, verificação real de e-mail, recuperação de senha e onboarding seguro.
- `24.11` — auditoria geral, segurança e regressão final.
- `24.12` — polimento visual, tema Claro/Escuro/Automático, chatbot especialista, experiência PWA tipo app, documentação e limpeza final.
- `25.0` — release comercial oficial.
- Pós-25.0 — estratégia estruturada de vendas e melhorias premium.

## Observação

O histórico detalhado das versões foi movido para `docs/historico/`; o planejamento completo está em `docs/ROADMAP.md`.
