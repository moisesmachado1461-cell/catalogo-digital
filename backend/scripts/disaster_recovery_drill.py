"""Executa um drill completo: backup -> verificação -> restore em banco separado.

Variáveis exigidas:
- BACKUP_DATABASE_URL: URL externa do banco de produção (somente leitura lógica no script)
- RESTORE_TEST_DATABASE_URL: banco PostgreSQL separado e descartável
- BACKUP_ENCRYPTION_KEY: chave Fernet

O banco RESTORE_TEST_DATABASE_URL será LIMPO pelo drill.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(args: list[str], env: dict[str, str]) -> None:
    print("+", " ".join(args))
    proc = subprocess.run(args, env=env, text=True)
    if proc.returncode:
        raise SystemExit(proc.returncode)


def main() -> int:
    required = ["BACKUP_DATABASE_URL", "RESTORE_TEST_DATABASE_URL", "BACKUP_ENCRYPTION_KEY"]
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        print("ERRO: variáveis ausentes: " + ", ".join(missing))
        return 2

    scripts = Path(__file__).resolve().parent
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="catalogo-drill-") as tmp:
        tmp_path = Path(tmp)
        run(
            [sys.executable, str(scripts / "backup_database.py"), "--non-interactive", "--require-encryption", "--output-dir", str(tmp_path)],
            env,
        )
        backups = sorted(tmp_path.glob("*.fernet"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not backups:
            print("ERRO: backup criptografado não foi criado.")
            return 1
        backup = backups[0]
        run([sys.executable, str(scripts / "verify_backup.py"), str(backup)], env)
        run(
            [
                sys.executable,
                str(scripts / "restore_database.py"),
                str(backup),
                "--migrate",
                "--wipe-existing-data",
                "--i-understand-this-deletes-target-data",
            ],
            env,
        )

    print()
    print("DRILL DE RECUPERAÇÃO CONCLUÍDO COM SUCESSO.")
    print("Produção não foi alterada; a restauração ocorreu somente no banco de teste configurado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
