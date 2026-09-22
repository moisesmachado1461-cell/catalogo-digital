# Catálogo Digital

SaaS multi-loja e multi-negócio para catálogo, pedidos, serviços, agendamentos, orçamentos, reservas, locações, pagamentos e gestão comercial.

**Versão de código atual:** `24.9.6`  
**Fase atual:** validação do Pix Marketplace em sandbox.

## Estrutura

- `backend/` — FastAPI, regras de negócio, integrações, migrations e testes.
- `frontend/` — loja pública, Cliente, Admin, Super Admin e PWA.
- `docs/` — arquitetura, status, roadmap, recuperação de desastre e histórico.
- `.github/` — automações e workflows.

## Validação antes de publicar

Na raiz do projeto:

```powershell
python backend\scripts\phase24_5_release_gate.py
```

Somente faça commit/push quando o release gate estiver aprovado no ambiente local configurado.

## Documentação principal

- `docs/STATUS_ATUAL.md` — ponto exato do projeto e próximo passo.
- `docs/ROADMAP.md` — continuidade até a versão 25.0 e melhorias futuras.
- `docs/ARQUITETURA_TECNICA_DEFINITIVA.md` — visão técnica.
- `docs/PLANO_RECUPERACAO_DESASTRE.md` — backup e recuperação.
- `CHANGELOG.md` — resumo das versões.
- `docs/historico/` — documentação das fases antigas e instruções incrementais.

## Segurança

Nunca versionar ou compartilhar `.env`, credenciais, tokens, bancos locais, uploads, backups ou chaves privadas. Esses itens são ignorados pelo Git e devem permanecer apenas em ambientes seguros.

## Fluxo oficial

Agrupar mudanças relacionadas, executar um release gate, fazer um commit/push, aguardar o Render e testar apenas os fluxos afetados.
