# Fase 18.1 — Cloudinary

O Catálogo Digital passa a aceitar `STORAGE_PROVIDER=cloudinary` para armazenar imagens de produção fora do filesystem efêmero do Render.

## Variáveis de ambiente no backend (Render)

- `STORAGE_PROVIDER=cloudinary`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

O `API Secret` nunca deve ser colocado no frontend, GitHub ou documentação pública.

## Fluxo

1. O administrador envia JPG/PNG/WebP.
2. O backend valida tamanho/tipo e converte para WebP.
3. O backend autenticado envia o WebP ao Cloudinary.
4. A URL HTTPS retornada pelo Cloudinary é salva/utilizada pelo Catálogo Digital.
5. `/api/health` informa `provider=cloudinary`, `persistent=true`, `configured=true`.

O modo local continua disponível para desenvolvimento e o modo S3 continua suportado.
