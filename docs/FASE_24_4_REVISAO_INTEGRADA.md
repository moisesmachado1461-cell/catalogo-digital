# Fase 24.4 — Revisão integrada Cliente + Admin + Super Admin

A Fase 24.4 formaliza a revisão integrada das três superfícies principais do Catálogo Digital sem alterar banco de dados.

## Objetivo

Garantir que a evolução visual das Fases 21, 22 e 23 continue conectada ao mesmo backend, com navegação, autenticação, componentes e comportamento responsivo coerentes antes da revisão manual final para lançamento.

## O que foi validado automaticamente

- presença das áreas Cliente/Loja, Admin e Super Admin;
- carregamento do Design System e dos CSS premium específicos;
- `viewport`, idioma e metadados essenciais nas três áreas;
- múltiplos breakpoints responsivos nas camadas premium;
- referências de IDs usadas pelo JavaScript, incluindo formulários/modais criados dinamicamente;
- autenticação baseada em JWT de sessão e limpeza do token em `401`;
- separação de papéis entre Admin e Super Admin no frontend;
- runtime compartilhado de API, UI e PWA;
- loja pública orientada por `capabilities`, mantendo os módulos de catálogo, serviços, cupons e pagamentos;
- alinhamento de versão/documentação da fase.

## Como executar

Dentro de `backend`, com Python disponível:

```powershell
python scripts/phase24_4_integrated_review.py
```

O script não usa o banco, não acessa credenciais e não precisa de internet.

## Resultado da revisão desta entrega

A auditoria integrada passou sem inconsistências estruturais detectáveis nas três áreas principais.

A auditoria geral da Fase 24 também permanece disponível em:

```powershell
python scripts/phase24_project_audit.py
```

A regressão funcional completa continua em:

```powershell
python scripts/phase24_2_functional_regression.py
```

Ela precisa das dependências de `requirements.txt` instaladas, pois cria um banco temporário, aplica migrations, executa seed e sobe a API local para validar os fluxos ponta a ponta.

## O que ainda precisa de validação manual

A automação não substitui a conferência visual real. Antes do lançamento, revisar em pelo menos:

- celular estreito (aprox. 360–390 px);
- celular grande (aprox. 430 px);
- tablet (aprox. 768–1024 px);
- notebook (aprox. 1366 px);
- desktop largo (aprox. 1440–1920 px).

Priorizar login, menu, modais, tabelas, formulários longos, carrinho/checkout, agendamento, reservas, locações, Meu Plano e Central de Cobrança.

## Banco de dados

Não há migration nova nesta fase.

## Versão

Backend: `24.4.0`.
