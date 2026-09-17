# Fase 24.5 — Validação final de produção

Objetivo: reduzir a validação pré-lançamento ao menor número de passos possível sem remover os testes que realmente protegem o projeto.

## 1. Antes do push — um comando

Na raiz do projeto, com a `.venv` ativa:

```powershell
python backend\scripts\phase24_5_release_gate.py
```

Esse comando executa automaticamente:

1. auditoria geral do código e segurança estrutural;
2. revisão integrada Cliente + Admin + Super Admin;
3. regressão funcional completa em banco SQLite temporário.

A regressão não toca no banco de produção.

## 2. Depois do deploy — um comando

Quando o Render estiver `Live`:

```powershell
python backend\scripts\production_smoke_check.py
```

As URLs oficiais já são padrão. O teste confirma:

- `/api/health` HTTP 200;
- versão online igual à versão local;
- `environment=production`;
- PostgreSQL respondendo;
- Cloudinary configurado e persistente;
- CORS da origem oficial;
- headers de segurança;
- homepage, loja, Admin, Super Admin e service worker.

O teste é somente leitura e não pede senhas.

## 3. Restore drill — uma vez antes do lançamento

No GitHub: `Actions` → `Restore drill do PostgreSQL` → `Run workflow`.

O workflow usa PostgreSQL temporário do próprio GitHub Actions. Ele precisa apenas dos secrets já documentados para backup.

## 4. Conferência visual mínima

Não é necessário testar dezenas de tamanhos. Antes do lançamento, faça uma passagem rápida em:

- desktop/notebook;
- celular.

Confira apenas loja pública, login Admin, dashboard Admin, login Super Admin e dashboard Super Admin.

## Resultado esperado

Se o release gate, o smoke de produção e o restore drill passarem, a base técnica está pronta para a etapa de domínio, SEO/PWA final e preparação comercial.

Sem migration. Backend `24.5.0`.
