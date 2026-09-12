"""Gate local único da Fase 24.5.

Executa somente os testes necessários antes do push:
1. auditoria geral do projeto;
2. revisão integrada Cliente/Admin/Super Admin;
3. regressão funcional isolada em banco temporário.

Nenhum dado de produção é alterado.

Uso a partir da raiz do projeto:
    python backend/scripts/phase24_5_release_gate.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SCRIPTS = BACKEND / "scripts"

CHECKS = [
    ("Auditoria geral", SCRIPTS / "phase24_project_audit.py"),
    ("Revisão integrada", SCRIPTS / "phase24_4_integrated_review.py"),
    ("Regressão funcional", SCRIPTS / "phase24_2_functional_regression.py"),
]


def run_check(label: str, script: Path) -> bool:
    print("\n" + "=" * 72, flush=True)
    print(label.upper(), flush=True)
    print("=" * 72, flush=True)
    result = subprocess.run([sys.executable, str(script)], cwd=BACKEND)
    return result.returncode == 0


def main() -> int:
    print("CATÁLOGO DIGITAL — FASE 24.5 · RELEASE GATE LOCAL", flush=True)
    for label, script in CHECKS:
        if not run_check(label, script):
            print(f"\n[ERRO] Gate interrompido em: {label}")
            return 1
    print("\n" + "=" * 72)
    print("[OK] RELEASE GATE APROVADO — pronto para commit/push e deploy.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
