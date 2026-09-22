"""Valida formato, contagens e hashes de um backup lógico.

Uso:
    python scripts/verify_backup.py backups/arquivo.json.gz
    BACKUP_ENCRYPTION_KEY="..." python scripts/verify_backup.py backups/arquivo.json.gz.fernet
"""
from __future__ import annotations

import argparse
from pathlib import Path

from backup_common import (
    BACKUP_FORMAT_V1,
    BACKUP_FORMAT_V2,
    get_encryption_key,
    load_backup,
    rows_for_table,
    table_digest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica backup lógico do Catálogo Digital")
    parser.add_argument("backup")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.backup).expanduser().resolve()
    if not path.exists():
        print(f"Arquivo não encontrado: {path}")
        return 2
    try:
        payload = load_backup(path, get_encryption_key())
    except Exception as exc:
        print(f"Backup inválido/corrompido: {exc}")
        return 1

    tables = payload.get("tables")
    if not isinstance(tables, dict) or not tables:
        print("Backup sem tabelas.")
        return 1

    total = 0
    errors: list[str] = []
    for name in sorted(tables):
        try:
            rows = rows_for_table(payload, name)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        total += len(rows)
        if payload.get("format") == BACKUP_FORMAT_V2:
            meta = tables[name]
            expected_count = meta.get("row_count")
            expected_hash = meta.get("sha256")
            if expected_count != len(rows):
                errors.append(f"{name}: contagem divergente ({expected_count} != {len(rows)})")
            if expected_hash != table_digest(rows):
                errors.append(f"{name}: SHA-256 divergente")
        print(f"[OK] {name}: {len(rows)} registro(s)")

    if payload.get("format") == BACKUP_FORMAT_V2 and payload.get("total_rows") != total:
        errors.append(f"total_rows divergente ({payload.get('total_rows')} != {total})")

    if errors:
        for error in errors:
            print(f"[ERRO] {error}")
        return 1

    print()
    print(f"Backup íntegro: formato={payload.get('format')}, {len(tables)} tabela(s), {total} registro(s).")
    if payload.get("schema_revision"):
        print(f"Revision Alembic de origem: {payload['schema_revision']}")
    if payload.get("format") == BACKUP_FORMAT_V1:
        print("Observação: backup legado v1; ele não possui hashes por tabela.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
