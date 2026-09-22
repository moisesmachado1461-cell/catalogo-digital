"""Restaura um backup lógico em um BANCO SEPARADO de recuperação/teste.

Proteções importantes:
- usa RESTORE_TEST_DATABASE_URL por padrão;
- recusa restaurar no mesmo banco que originou o backup (fingerprint);
- exige banco vazio, a menos que flags destrutivas explícitas sejam fornecidas;
- mantém alembic_version do schema atual e não restaura essa tabela.

Exemplo:
    RESTORE_TEST_DATABASE_URL="..." BACKUP_ENCRYPTION_KEY="..." \
      python scripts/restore_database.py backups/arquivo.json.gz.fernet --migrate
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import MetaData, create_engine, delete, func, select, text

from backup_common import database_fingerprint, deserialize, get_encryption_key, load_backup, normalize_database_url, rows_for_table

SKIP_TABLES = {"alembic_version"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restaura backup em banco separado")
    parser.add_argument("backup")
    parser.add_argument("--database-url-env", default="RESTORE_TEST_DATABASE_URL")
    parser.add_argument("--migrate", action="store_true", help="executa alembic upgrade head no banco alvo antes da restauração")
    parser.add_argument("--wipe-existing-data", action="store_true", help="apaga dados existentes do banco alvo")
    parser.add_argument(
        "--i-understand-this-deletes-target-data",
        action="store_true",
        help="confirma a limpeza quando --wipe-existing-data for usado",
    )
    return parser.parse_args()


def target_has_data(connection, metadata: MetaData) -> bool:
    for table in metadata.sorted_tables:
        if table.name in SKIP_TABLES:
            continue
        count = connection.execute(select(func.count()).select_from(table)).scalar_one()
        if count:
            return True
    return False


def reset_sequences(connection, metadata: MetaData) -> None:
    if connection.dialect.name != "postgresql":
        return
    for table in metadata.sorted_tables:
        if table.name in SKIP_TABLES:
            continue
        for column in table.primary_key.columns:
            if not getattr(column.type, "python_type", None) is int:
                continue
            seq = connection.execute(
                text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
                {"table_name": table.fullname, "column_name": column.name},
            ).scalar_one_or_none()
            if not seq:
                continue
            max_value = connection.execute(select(func.max(column))).scalar_one_or_none()
            if max_value is None:
                connection.execute(text("SELECT setval(:seq, 1, false)"), {"seq": seq})
            else:
                connection.execute(text("SELECT setval(:seq, :value, true)"), {"seq": seq, "value": int(max_value)})


def run_migrations(database_url: str) -> None:
    backend = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env.setdefault("ENVIRONMENT", "development")
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend,
        env=env,
        text=True,
    )
    if proc.returncode:
        raise RuntimeError("alembic upgrade head falhou no banco de recuperação")


def main() -> int:
    args = parse_args()
    backup_path = Path(args.backup).expanduser().resolve()
    if not backup_path.exists():
        print(f"ERRO: backup não encontrado: {backup_path}")
        return 2

    target_raw = os.getenv(args.database_url_env, "").strip()
    if not target_raw:
        print(f"ERRO: defina {args.database_url_env} com a URL do banco SEPARADO de recuperação.")
        return 2
    target_url = normalize_database_url(target_raw)

    try:
        payload = load_backup(backup_path, get_encryption_key())
    except Exception as exc:
        print(f"ERRO ao abrir backup: {exc}")
        return 1

    source_fingerprint = payload.get("database_fingerprint")
    if source_fingerprint and source_fingerprint == database_fingerprint(target_raw):
        print("ERRO DE SEGURANÇA: o banco alvo parece ser o mesmo banco que originou o backup.")
        print("Use sempre um banco separado para o restore drill.")
        return 1

    if args.wipe_existing_data and not args.i_understand_this_deletes_target_data:
        print("ERRO: --wipe-existing-data exige --i-understand-this-deletes-target-data.")
        return 2

    if args.migrate:
        try:
            run_migrations(target_raw)
        except Exception as exc:
            print(f"ERRO nas migrations do alvo: {exc}")
            return 1

    engine = create_engine(target_url, pool_pre_ping=True)
    metadata = MetaData()
    try:
        with engine.connect() as connection:
            metadata.reflect(bind=connection)
        if not metadata.tables:
            print("ERRO: banco alvo sem schema. Use --migrate ou aplique as migrations antes.")
            return 1

        backup_tables = set(payload.get("tables", {})) - SKIP_TABLES
        target_tables = {t.name for t in metadata.sorted_tables} - SKIP_TABLES
        missing = sorted(backup_tables - target_tables)
        if missing:
            print("ERRO: tabelas do backup não existem no alvo: " + ", ".join(missing))
            return 1

        with engine.begin() as connection:
            has_data = target_has_data(connection, metadata)
            if has_data and not args.wipe_existing_data:
                raise RuntimeError("Banco alvo contém dados. Use um banco vazio ou flags explícitas de limpeza.")

            if has_data:
                for table in reversed(metadata.sorted_tables):
                    if table.name not in SKIP_TABLES:
                        connection.execute(delete(table))

            restored = 0
            for table in metadata.sorted_tables:
                if table.name in SKIP_TABLES or table.name not in backup_tables:
                    continue
                rows = rows_for_table(payload, table.name)
                allowed = set(table.c.keys())
                decoded = [
                    {key: deserialize(value) for key, value in row.items() if key in allowed}
                    for row in rows
                ]
                if decoded:
                    connection.execute(table.insert(), decoded)
                restored += len(decoded)
                print(f"  RESTAURADO {table.name}: {len(decoded)} registro(s)")

            reset_sequences(connection, metadata)

            # Verificação de contagens dentro da mesma transação.
            for table in metadata.sorted_tables:
                if table.name in SKIP_TABLES or table.name not in backup_tables:
                    continue
                expected = len(rows_for_table(payload, table.name))
                actual = connection.execute(select(func.count()).select_from(table)).scalar_one()
                if actual != expected:
                    raise RuntimeError(f"Contagem divergente em {table.name}: {actual} != {expected}")

        print()
        print(f"Restore concluído e validado: {restored} registro(s).")
        print("IMPORTANTE: o banco restaurado é apenas de recuperação/teste; não troque produção automaticamente.")
        return 0
    except Exception as exc:
        print(f"ERRO no restore: {exc}")
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
