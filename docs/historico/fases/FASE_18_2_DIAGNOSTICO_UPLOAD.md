# Fase 18.2 — Diagnóstico seguro de upload

Este patch não altera banco de dados.

Ele adiciona logs seguros ao endpoint de upload para revelar no Render a causa técnica real
do erro do Cloudinary, sem exibir API Secret, API Key, JWT ou DATABASE_URL.

Depois de publicar o patch:
1. Tente enviar uma imagem pelo Admin online.
2. Abra Render > catalogo-digital-api > Logs.
3. Procure por `upload_storage_failed`.
4. Copie somente essa linha para diagnóstico.
