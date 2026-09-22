"""
Migração segura do Catálogo Digital:
SQLite local (catalogo.db) -> PostgreSQL de produção.

Versão 2:
- Continua bloqueando se houver dados reais no PostgreSQL.
- Se os ÚNICOS dados online forem registros em audit_logs, permite limpá-los
  com confirmação explícita e continuar a migração.

Uso:
    1) Coloque este arquivo dentro da pasta backend.
    2) Ative o .venv.
    3) Execute:
           python migrar_sqlite_para_postgres_v2.py
    4) Quando solicitado, cole a EXTERNAL Database URL do PostgreSQL do Render.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

from sqlalchemy import (
    Integer,
    MetaData,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.exc import SQLAlchemyError


SOURCE_FILENAME = "catalogo.db"
BACKUP_FILENAME = "catalogo-backup-antes-producao.db"
ALEMBIC_TABLE = "alembic_version"
AUDIT_TABLE = "audit_logs"
BATCH_SIZE = 500


def normalize_postgres_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgresql+psycopg://"):
        return url
    raise ValueError(
        "A URL informada não parece ser uma URL PostgreSQL válida do Render."
    )


def get_alembic_version(conn) -> str | None:
    try:
        return conn.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar_one_or_none()
    except Exception:
        return None


def count_rows(conn, table) -> int:
    return int(conn.execute(select(func.count()).select_from(table)).scalar_one())


def sanitize_error(message: str, secrets: list[str]) -> str:
    result = message
    for secret in secrets:
        if secret:
            result = result.replace(secret, "[URL OCULTA]")
    return result


def main() -> int:
    print("=" * 72)
    print(" CATÁLOGO DIGITAL — MIGRAÇÃO SQLITE -> POSTGRESQL (V2)")
    print("=" * 72)
    print()
    print("Este processo COPIA os dados. O catalogo.db local não será apagado.")
    print("O PostgreSQL deve estar vazio, exceto por audit_logs gerados nos testes.")
    print()

    source_path = Path(SOURCE_FILENAME).resolve()
    backup_path = source_path.with_name(BACKUP_FILENAME)

    if not source_path.exists():
        print(f"ERRO: não encontrei {SOURCE_FILENAME}.")
        print("Coloque este script dentro da pasta backend e execute por lá.")
        return 1

    if not backup_path.exists():
        print(f"ERRO: não encontrei {BACKUP_FILENAME}.")
        print("Faça o backup antes de continuar.")
        return 1

    print(f"Banco local encontrado: {source_path.name}")
    print(f"Backup encontrado:      {backup_path.name}")
    print()
    print("No Render, abra catalogo-digital-db e copie a:")
    print("  External Database URL")
    print()
    print("A URL ficará oculta enquanto você cola.")
    remote_raw = getpass.getpass("Cole a External Database URL do Render: ").strip()

    try:
        remote_url = normalize_postgres_url(remote_raw)
    except ValueError as exc:
        print(f"\nERRO: {exc}")
        return 1

    sqlite_url = f"sqlite:///{source_path.as_posix()}"

    source_engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
    )
    target_engine = create_engine(
        remote_url,
        pool_pre_ping=True,
    )

    try:
        print("\nConectando aos bancos...")

        with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
            source_version = get_alembic_version(source_conn)
            target_version = get_alembic_version(target_conn)

            print(f"Migration local:  {source_version or 'não encontrada'}")
            print(f"Migration online: {target_version or 'não encontrada'}")

            if not source_version or not target_version:
                print("\nERRO: não foi possível confirmar a versão do Alembic nos dois bancos.")
                return 1

            if source_version != target_version:
                print("\nERRO: as migrations local e online são diferentes.")
                print("Não faremos a cópia para evitar inconsistência.")
                return 1

            source_meta = MetaData()
            target_meta = MetaData()
            source_meta.reflect(bind=source_conn)
            target_meta.reflect(bind=target_conn)

            target_tables = [
                table for table in target_meta.sorted_tables
                if table.name != ALEMBIC_TABLE
            ]

            missing_source = [
                table.name for table in target_tables
                if table.name not in source_meta.tables
            ]
            if missing_source:
                print("\nERRO: existem tabelas no PostgreSQL que não existem no SQLite:")
                for name in missing_source:
                    print(f"  - {name}")
                return 1

            non_empty_target = []
            for table in target_tables:
                qty = count_rows(target_conn, table)
                if qty:
                    non_empty_target.append((table.name, qty))

        # Se só existirem audit_logs online, eles são resíduos dos testes de login
        # feitos antes da importação. Permitimos limpá-los com confirmação explícita.
        if non_empty_target:
            only_audit_logs = all(name == AUDIT_TABLE for name, _ in non_empty_target)

            if not only_audit_logs:
                print("\nPARADO POR SEGURANÇA.")
                print("O PostgreSQL online já possui dados além de audit_logs:")
                for name, qty in non_empty_target:
                    print(f"  - {name}: {qty} registro(s)")
                print()
                print("Este script não mistura nem sobrescreve dados existentes.")
                return 2

            audit_count = non_empty_target[0][1]
            print()
            print("Foram encontrados somente registros de auditoria no banco online:")
            print(f"  - {AUDIT_TABLE}: {audit_count} registro(s)")
            print()
            print("Isso normalmente acontece porque o login online foi testado antes")
            print("de importar os usuários do banco local.")
            print()
            confirmation = input(
                "Digite LIMPAR_AUDIT para apagar SOMENTE esses logs e continuar: "
            ).strip()

            if confirmation != "LIMPAR_AUDIT":
                print("\nOperação cancelada. Nenhum dado foi alterado.")
                return 0

            with target_engine.begin() as target_conn:
                target_conn.execute(text(f"DELETE FROM {AUDIT_TABLE}"))

            print(f"\n{audit_count} registro(s) de audit_logs removido(s).")
            print("Nenhuma outra tabela foi alterada.")

        # Recarrega metadados e confirma que o destino agora está vazio.
        with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
            source_meta = MetaData()
            target_meta = MetaData()
            source_meta.reflect(bind=source_conn)
            target_meta.reflect(bind=target_conn)

            target_tables = [
                table for table in target_meta.sorted_tables
                if table.name != ALEMBIC_TABLE
            ]

            remaining = []
            for table in target_tables:
                qty = count_rows(target_conn, table)
                if qty:
                    remaining.append((table.name, qty))

            if remaining:
                print("\nPARADO POR SEGURANÇA.")
                print("Ainda existem dados no PostgreSQL:")
                for name, qty in remaining:
                    print(f"  - {name}: {qty} registro(s)")
                return 2

            total_rows = 0
            source_counts = {}
            for target_table in target_tables:
                source_table = source_meta.tables[target_table.name]
                qty = count_rows(source_conn, source_table)
                source_counts[target_table.name] = qty
                total_rows += qty

            print()
            print(f"Tabelas a copiar: {len(target_tables)}")
            print(f"Registros totais: {total_rows}")
            print()
            print("Nenhum dado do SQLite foi alterado.")
            confirmation = input(
                "Digite MIGRAR para iniciar a cópia para o PostgreSQL: "
            ).strip()

            if confirmation != "MIGRAR":
                print("\nMigração cancelada.")
                return 0

        print("\nIniciando migração...")

        # Transação única: qualquer falha durante a cópia reverte tudo.
        with source_engine.connect() as source_conn, target_engine.begin() as target_conn:
            source_meta = MetaData()
            target_meta = MetaData()
            source_meta.reflect(bind=source_conn)
            target_meta.reflect(bind=target_conn)

            target_tables = [
                table for table in target_meta.sorted_tables
                if table.name != ALEMBIC_TABLE
            ]

            for target_table in target_tables:
                source_table = source_meta.tables[target_table.name]
                target_columns = {column.name for column in target_table.columns}

                result = source_conn.execute(select(source_table))
                batch = []

                for row in result.mappings():
                    record = {
                        key: value
                        for key, value in row.items()
                        if key in target_columns
                    }
                    batch.append(record)

                    if len(batch) >= BATCH_SIZE:
                        target_conn.execute(target_table.insert(), batch)
                        batch.clear()

                if batch:
                    target_conn.execute(target_table.insert(), batch)

                qty = source_counts.get(target_table.name, 0)
                print(f"  OK  {target_table.name:<34} {qty:>6} registro(s)")

            # Sincroniza sequences do PostgreSQL após copiar IDs explícitos.
            for table in target_tables:
                pk_columns = list(table.primary_key.columns)
                if len(pk_columns) != 1:
                    continue

                pk = pk_columns[0]
                if not isinstance(pk.type, Integer):
                    continue

                max_id = target_conn.execute(
                    select(func.max(pk))
                ).scalar_one_or_none()

                if max_id is None:
                    continue

                sequence_name = target_conn.execute(
                    text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
                    {"table_name": table.name, "column_name": pk.name},
                ).scalar_one_or_none()

                if sequence_name:
                    target_conn.execute(
                        text(
                            "SELECT setval(CAST(:sequence_name AS regclass), "
                            ":max_id, true)"
                        ),
                        {
                            "sequence_name": sequence_name,
                            "max_id": int(max_id),
                        },
                    )

        print("\nVerificando o resultado...")
        differences = []

        with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
            source_meta = MetaData()
            target_meta = MetaData()
            source_meta.reflect(bind=source_conn)
            target_meta.reflect(bind=target_conn)

            for name, source_table in source_meta.tables.items():
                if name == ALEMBIC_TABLE or name not in target_meta.tables:
                    continue

                source_qty = count_rows(source_conn, source_table)
                target_qty = count_rows(target_conn, target_meta.tables[name])

                if source_qty != target_qty:
                    differences.append((name, source_qty, target_qty))

        if differences:
            print("\nATENÇÃO: encontramos diferenças de contagem:")
            for name, local_qty, online_qty in differences:
                print(f"  - {name}: local={local_qty}, online={online_qty}")
            return 3

        print()
        print("=" * 72)
        print(" MIGRAÇÃO CONCLUÍDA COM SUCESSO")
        print("=" * 72)
        print(f"Registros copiados: {total_rows}")
        print("O catalogo.db e o backup continuam intactos no computador.")
        print()
        print("Próximo passo:")
        print("  1) Abra o admin online.")
        print("  2) Entre com seu usuário local.")
        print("  3) Confira lojas, serviços, produtos e agendamentos.")
        print()
        print("As imagens da pasta uploads ainda não são transferidas por este script.")
        return 0

    except (SQLAlchemyError, OSError, ValueError) as exc:
        safe_message = sanitize_error(str(exc), [remote_raw, remote_url])
        print("\nERRO DURANTE A MIGRAÇÃO:")
        print(safe_message)
        print()
        print("O SQLite local não foi apagado.")
        print("Se a falha aconteceu durante a cópia, a transação do PostgreSQL")
        print("foi revertida automaticamente.")
        return 4

    finally:
        source_engine.dispose()
        target_engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
