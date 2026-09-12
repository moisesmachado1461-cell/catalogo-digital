"""Utilitários compartilhados dos backups do Catálogo Digital.

Este módulo não imprime nem persiste URLs completas do banco.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken

BACKUP_FORMAT_V1 = "catalogo-digital-logical-backup-v1"
BACKUP_FORMAT_V2 = "catalogo-digital-logical-backup-v2"
SUPPORTED_FORMATS = {BACKUP_FORMAT_V1, BACKUP_FORMAT_V2}


def normalize_database_url(url: str) -> str:
    value = url.strip()
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://"):]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://"):]
    if value.startswith("postgresql+psycopg://") or value.startswith("sqlite:"):
        return value
    raise ValueError("DATABASE URL inválida. Use PostgreSQL ou SQLite local para testes.")


def database_fingerprint(url: str) -> str:
    """Hash não reversível do destino, sem gravar credenciais no backup."""
    value = normalize_database_url(url)
    if value.startswith("sqlite:"):
        identity = value
    else:
        parsed = urlsplit(value.replace("postgresql+psycopg://", "postgresql://", 1))
        identity = f"{parsed.hostname or ''}:{parsed.port or 5432}/{parsed.path.lstrip('/')}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


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


def deserialize(value):
    if not isinstance(value, dict) or "__type__" not in value:
        return value
    kind = value.get("__type__")
    raw = value.get("value")
    if kind == "decimal":
        return Decimal(raw)
    if kind == "datetime":
        return datetime.fromisoformat(raw)
    if kind == "date":
        return date.fromisoformat(raw)
    if kind == "time":
        return time.fromisoformat(raw)
    if kind == "uuid":
        return UUID(raw)
    if kind == "bytes":
        return base64.b64decode(raw.encode("ascii"))
    return raw


def canonical_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def table_digest(rows: list[dict]) -> str:
    return hashlib.sha256(canonical_json(rows)).hexdigest()


def get_encryption_key(env_name: str = "BACKUP_ENCRYPTION_KEY") -> str | None:
    value = os.getenv(env_name, "").strip()
    return value or None


def validate_fernet_key(key: str) -> bytes:
    raw = key.encode("ascii")
    # A construção já valida base64/tamanho; encrypt/decrypt usa a chave pronta.
    Fernet(raw)
    return raw


def encode_payload(payload: dict, encryption_key: str | None = None) -> bytes:
    compressed = gzip.compress(canonical_json(payload), compresslevel=6)
    if not encryption_key:
        return compressed
    return Fernet(validate_fernet_key(encryption_key)).encrypt(compressed)


def decode_backup_bytes(raw: bytes, encrypted: bool, encryption_key: str | None = None) -> dict:
    try:
        if encrypted:
            if not encryption_key:
                raise ValueError("Backup criptografado: defina BACKUP_ENCRYPTION_KEY.")
            try:
                raw = Fernet(validate_fernet_key(encryption_key)).decrypt(raw)
            except InvalidToken as exc:
                raise ValueError("Chave de backup incorreta ou arquivo criptografado corrompido.") from exc
        data = gzip.decompress(raw)
        payload = json.loads(data.decode("utf-8"))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Backup inválido/corrompido: {exc}") from exc
    if payload.get("format") not in SUPPORTED_FORMATS:
        raise ValueError("Formato de backup não reconhecido.")
    return payload


def load_backup(path: Path, encryption_key: str | None = None) -> dict:
    raw = path.read_bytes()
    encrypted = path.name.endswith((".fernet", ".enc"))
    return decode_backup_bytes(raw, encrypted=encrypted, encryption_key=encryption_key)


def rows_for_table(payload: dict, table_name: str) -> list[dict]:
    table_data = payload.get("tables", {}).get(table_name, [])
    if isinstance(table_data, list):  # legado v1
        return table_data
    if isinstance(table_data, dict) and isinstance(table_data.get("rows"), list):
        return table_data["rows"]
    raise ValueError(f"Estrutura inválida da tabela {table_name!r} no backup.")
