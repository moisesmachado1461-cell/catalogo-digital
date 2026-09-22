"""Executa uma passagem do motor de cobrança de assinaturas.

Uso a partir da pasta backend:
    python scripts/process_subscription_billing.py

Nesta fase o script NÃO chama bancos/gateways externos. Ele apenas mantém o
ciclo interno, gera faturas pendentes, aplica tolerância e expiração.
"""
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.services.billing_service import process_due_billing  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        stats = process_due_billing(db)
        db.commit()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
