from __future__ import annotations

from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from ..config import settings
from ..dependencies import get_current_store_id
from ..storage import get_storage

router = APIRouter(prefix="/api/admin/uploads", tags=["uploads-admin"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 40_000_000
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
KIND_LIMITS = {
    "logo": (900, 900),
    "banner": (2000, 1000),
    "product": (1600, 1600),
    "category": (1600, 1200),
    "service": (1600, 1200),
    "professional": (1200, 1200),
    "resource": (1600, 1200),
}


def _process_image(raw: bytes, kind: str) -> tuple[bytes, int, int]:
    try:
        with Image.open(BytesIO(raw)) as probe:
            probe.verify()
        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
                raise HTTPException(status_code=413, detail="Imagem possui dimensões muito grandes")

            max_width, max_height = KIND_LIMITS[kind]
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                image = image.convert("RGBA")
            else:
                image = image.convert("RGB")

            out = BytesIO()
            image.save(out, format="WEBP", quality=86, method=6)
            final_width, final_height = image.size
            return out.getvalue(), final_width, final_height
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=415, detail="Arquivo de imagem inválido")


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    kind: str = Form(...),
    file: UploadFile = File(...),
    store_id: int = Depends(get_current_store_id),
):
    kind = kind.strip().lower()
    if kind not in KIND_LIMITS:
        raise HTTPException(status_code=422, detail="Tipo de imagem não suportado")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Envie uma imagem JPG, PNG ou WebP")

    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if not raw:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="A imagem deve ter no máximo 8 MB")

    processed, width, height = _process_image(raw, kind)
    filename = f"{uuid4().hex}.webp"
    key = f"store_{store_id}/{kind}/{filename}"
    base_url = settings.public_api_base_url or str(request.base_url).rstrip("/")

    try:
        stored = get_storage().save(
            key=key,
            data=processed,
            content_type="image/webp",
            base_url=base_url,
        )
    except Exception as exc:
        # Não devolvemos detalhes/credenciais do provedor ao navegador.
        raise HTTPException(status_code=503, detail="Não foi possível salvar a imagem no momento") from exc

    return {
        "url": stored.url,
        "path": stored.path,
        "provider": stored.provider,
        "kind": kind,
        "width": width,
        "height": height,
        "size_bytes": len(processed),
    }
