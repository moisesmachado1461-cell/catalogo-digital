# Fase 24.2 — Testes funcionais e isolamento multi-tenant

Esta etapa adiciona uma regressão funcional automatizada que **não toca no banco de produção**.
O script cria um SQLite temporário, aplica todas as migrations, executa o seed, sobe a API
localmente em uma porta livre e remove tudo ao terminar.

## O que é validado

- health e versão da API;
- login de Super Admin e administradores de lojas;
- vínculo correto de `store_id` por usuário;
- isolamento real de catálogo entre Mercado e Loja Tech;
- bloqueio de acesso direto a produto pertencente a outra loja;
- proibição de Admin acessar rotas de Super Admin e vice-versa;
- catálogo público por slug;
- serviços/profissionais da barbearia;
- recursos de reserva da pousada;
- itens de locação;
- rotas administrativas de serviços, orçamentos, reservas e locações;
- edição de loja pelo Super Admin;
- criação de cupom de produto, exposição pública e bloqueio de produto cross-tenant;
- criação de cupom de plano no Super Admin e validação pelo Admin;
- assinatura, Meu Plano e Central de Cobrança em modo leitura;
- retorno 404 para loja inexistente.

## Como executar manualmente

Dentro de `backend`, com a `.venv` ativada:

```powershell
python scripts/phase24_2_functional_regression.py
```

Resultado esperado:

```text
CATÁLOGO DIGITAL — FASE 24.2
Resultado: 15 verificações funcionais OK, 0 erros.
Banco e servidor usados no teste eram temporários e já foram removidos.
```

O script usa somente contas demo criadas pelo próprio `seed.py`; nenhuma credencial de produção é lida.

## Migration

Não há migration nova na Fase 24.2.
