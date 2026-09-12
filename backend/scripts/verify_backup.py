"""Valida integridade estrutural de um backup lógico .json.gz sem restaurá-lo.

Uso:
    python scripts/verify_backup.py backups/catalogo-postgres-AAAAmmdd-HHMMSS.json.gz
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python scripts/verify_backup.py <arquivo.json.gz>")
        return 2
    path = Path(sys.argv[1]).expanduser().resolve()
    if not path.exists():
        print(f"Arquivo não encontrado: {path}")
        return 2
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        print(f"Backup inválido/corrompido: {exc}")
        return 1

    if payload.get("format") != "catalogo-digital-logical-backup-v1":
        print("Formato de backup não reconhecido.")
        return 1
    tables = payload.get("tables")
    if not isinstance(tables, dict) or not tables:
        print("Backup sem tabelas.")
        return 1

    total = 0
    malformed = []
    for name, rows in sorted(tables.items()):
        if not isinstance(rows, list):
            malformed.append(name)
            continue
        total += len(rows)
        print(f"[OK] {name}: {len(rows)} registro(s)")
    if malformed:
        print("Tabelas com estrutura inválida: " + ", ".join(malformed))
        return 1
    print()
    print(f"Backup íntegro estruturalmente: {len(tables)} tabela(s), {total} registro(s).")
    print("Observação: esta validação não substitui um teste real de restauração em banco separado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
