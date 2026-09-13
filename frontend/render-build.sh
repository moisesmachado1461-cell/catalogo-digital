#!/usr/bin/env bash
set -euo pipefail

if [ -z "${API_BASE_URL:-}" ]; then
  echo "ERRO: defina API_BASE_URL com a URL pública do backend, por exemplo https://catalogo-digital-api.onrender.com"
  exit 1
fi

rm -rf dist
mkdir -p dist

# Copia diretórios completos para preservar subpastas como js/shared/.
cp -R css dist/css
cp -R icons dist/icons
cp -R js dist/js
cp *.html dist/
cp manifest.webmanifest service-worker.js dist/

API_BASE_CLEAN="${API_BASE_URL%/}"
cat > dist/js/runtime-config.js <<EOF_RUNTIME
window.CATALOGO_CONFIG = { apiBase: "${API_BASE_CLEAN}" };
EOF_RUNTIME

echo "Frontend preparado para API: ${API_BASE_CLEAN}"
