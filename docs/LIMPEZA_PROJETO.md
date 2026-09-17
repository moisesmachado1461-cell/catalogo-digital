# Limpeza estrutural do projeto — 17/09/2026

A limpeza foi feita sem alterar as regras de negócio nem remover dados locais necessários para continuar o desenvolvimento.

## Removido com segurança

- `__pycache__`, `.pyc`, `.pyo` e caches de ferramentas;
- arquivos temporários/logs locais;
- `assistant-test.json` (payload manual de teste, sem referência no sistema);
- diretório `scripts/` vazio da raiz;
- placeholder de backup SQLite com 0 bytes;
- estrutura duplicada antiga que existia fora da pasta principal no ZIP recebido.

## Reorganizado

- `INSTALAR_FASE_*.txt` e antigos `LEIA_*.txt` foram movidos para `docs/historico/instalacao/`;
- `docs/FASE_*.md` foram movidos para `docs/historico/fases/`;
- `ROADMAP_COMPLETO_CATALOGO_DIGITAL.md` virou `docs/ROADMAP.md`;
- `docs/STATUS_ATUAL.md` foi condensado para mostrar apenas o estado atual e os próximos passos;
- `README.md` foi transformado no README principal do produto;
- criado `CHANGELOG.md`;
- criado `docs/README.md` para explicar a organização da documentação.

## Preservado de propósito

Para que esta cópia continue sendo utilizável no computador atual, foram preservados:

- `.git/` e histórico do repositório;
- `backend/.venv/`;
- `backend/.env` local;
- bancos SQLite locais;
- `backend/uploads/`;
- `backend/backups/`;
- todo o código, migrations, testes e scripts operacionais.

Esses itens continuam protegidos pelo `.gitignore` e não devem ser enviados ao GitHub quando forem arquivos locais/privados.

## Validação realizada

Após a limpeza:

- auditoria geral: **11 OK / 0 erros**;
- revisão integrada: **9 OK / 0 erros**;
- Python: sintaxe válida em 91 arquivos;
- JavaScript: sintaxe válida em 13 arquivos;
- Alembic head: `020_store_marketplace_payments`;
- versão central: `24.9.6`.

A regressão funcional completa deve ser executada no Windows do projeto usando o ambiente virtual local:

```powershell
python backend\scripts\phase24_5_release_gate.py
```

## Fase atual

`24.9.6 — Pix Marketplace sandbox`.
