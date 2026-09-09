"""Backup lógico simples do PostgreSQL do Catálogo Digital.

Este utilitário foi pensado como uma camada extra de segurança para bancos
pequenos. Para produção comercial, use também backups automáticos gerenciados
pelo provedor do PostgreSQL.

Execute dentro de backend com o .venv ativo:
    python scripts/backup_database.py

Quando solicitado, cole a EXTERNAL Database URL do Render. A URL fica oculta.
O arquivo é criado em backend/backups/ e essa pasta é ignorada pelo Git.
"""

from __future__ import annotations

import base64
import gzip
import getpass
import json
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import MetaData, create_engine, select


def normalize_url(url: str) -> str:
    value = url.strip()
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://"):]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://"):]
    if value.startswith("postgresql+psycopg://"):
        return value
    raise ValueError("URL PostgreSQL inválida")


def serialize(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return {"__type__": "decimal", "value": str(value)}
    if isinstance(value, datetime):
        return {"__type__": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"__type__": "date", "value": value.isoformat()}
    if isinstance(value, time):
        return {"__type__": "time", "value": value.isoformat()}
    if isinstance(value, UUID):
        return {"__type__": "uuid", "value": str(value)}
    if isinstance(value, bytes):
        return {"__type__": "bytes", "value": base64.b64encode(value).decode("ascii")}
    return {"__type__": type(value).__name__, "value": str(value)}


def main() -> None:
    print("CATÁLOGO DIGITAL — BACKUP LÓGICO DO POSTGRESQL")
    print("Use a External Database URL do Render. Ela não será exibida.")
    raw_url = getpass.getpass("External Database URL: ").strip()
    url = normalize_url(raw_url)

    engine = create_engine(url, pool_pre_ping=True)
    metadata = MetaData()

    output_dir = Path(__file__).resolve().parents[1] / "backups"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"catalogo-postgres-{timestamp}.json.gz"

    try:
        with engine.connect() as connection:
            metadata.reflect(bind=connection)
            payload = {
                "format": "catalogo-digital-logical-backup-v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "tables": {},
            }

            total = 0
            for table in metadata.sorted_tables:
                rows = []
                for row in connection.execute(select(table)).mappings():
                    rows.append({key: serialize(value) for key, value in row.items()})
                payload["tables"][table.name] = rows
                total += len(rows)
                print(f"  OK {table.name}: {len(rows)} registro(s)")

        with gzip.open(output_path, "wt", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))

        print()
        print(f"Backup concluído: {output_path}")
        print(f"Registros exportados: {total}")
        print("Guarde uma cópia fora do computador principal.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
