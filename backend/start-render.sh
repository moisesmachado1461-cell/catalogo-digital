#!/usr/bin/env bash
set -euo pipefail

echo "Aplicando migrations..."
alembic upgrade head

echo "Iniciando Catálogo Digital..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
