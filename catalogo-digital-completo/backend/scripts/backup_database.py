"""Backup lógico, verificável e opcionalmente criptografado.

Produção (não interativo, recomendado):
    BACKUP_DATABASE_URL="..." BACKUP_ENCRYPTION_KEY="..." \
      python scripts/backup_database.py --non-interactive --require-encryption

Uso manual:
    python scripts/backup_database.py

A URL nunca é gravada no arquivo. Backups automatizados devem ser criptografados.
Este backup é uma camada adicional e não substitui snapshots/PITR do provedor.
"""
from __future__ import annotations

import argparse
import getpass
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import MetaData, create_engine, select, text

from backup_common import (
    BACKUP_FORMAT_V2,
    database_fingerprint,
    encode_payload,
    get_encryption_key,
    normalize_database_url,
    serialize,
    table_digest,
)


def read_schema_revision(connection) -> str | None:
    try:
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    except Exception:
        return None


def create_backup(database_url: str, output_dir: Path, encryption_key: str | None) -> Path:
    url = normalize_database_url(database_url)
    engine = create_engine(url, pool_pre_ping=True)
    metadata = MetaData()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = ".json.gz.fernet" if encryption_key else ".json.gz"
    output_path = output_dir / f"catalogo-postgres-{timestamp}{suffix}"

    try:
        with engine.connect() as connection:
            metadata.reflect(bind=connection)
            payload = {
                "format": BACKUP_FORMAT_V2,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "schema_revision": read_schema_revision(connection),
                "database_dialect": engine.dialect.name,
                "database_fingerprint": database_fingerprint(database_url),
                "tables": {},
                "total_rows": 0,
            }
            for table in metadata.sorted_tables:
                rows = [
                    {key: serialize(value) for key, value in row.items()}
                    for row in connection.execute(select(table)).mappings()
                ]
                payload["tables"][table.name] = {
                    "row_count": len(rows),
                    "sha256": table_digest(rows),
                    "rows": rows,
                }
                payload["total_rows"] += len(rows)
                print(f"  OK {table.name}: {len(rows)} registro(s)")

        output_path.write_bytes(encode_payload(payload, encryption_key=encryption_key))
        return output_path
    finally:
        engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backup lógico do Catálogo Digital")
    parser.add_argument("--non-interactive", action="store_true", help="usa BACKUP_DATABASE_URL/DATABASE_URL")
    parser.add_argument("--output-dir", default=None, help="pasta de saída; padrão backend/backups")
    parser.add_argument("--require-encryption", action="store_true", help="falha se BACKUP_ENCRYPTION_KEY não estiver definido")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("CATÁLOGO DIGITAL — BACKUP LÓGICO")

    if args.non_interactive:
        raw_url = os.getenv("BACKUP_DATABASE_URL", "").strip() or os.getenv("DATABASE_URL", "").strip()
        if not raw_url:
            print("ERRO: defina BACKUP_DATABASE_URL (preferível) ou DATABASE_URL.")
            return 2
    else:
        print("Use a External Database URL do PostgreSQL. Ela não será exibida nem salva.")
        raw_url = getpass.getpass("Database URL: ").strip()

    key = get_encryption_key()
    if args.require_encryption and not key:
        print("ERRO: BACKUP_ENCRYPTION_KEY é obrigatório para este backup.")
        return 2

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path(__file__).resolve().parents[1] / "backups"
    try:
        path = create_backup(raw_url, output_dir, key)
    except Exception as exc:
        print(f"ERRO no backup: {exc}")
        return 1

    print()
    print(f"Backup concluído: {path}")
    print("Criptografia: ATIVA" if key else "Criptografia: NÃO ATIVA (uso manual/local)")
    print("Guarde cópias fora do computador principal e valide restauração periodicamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
