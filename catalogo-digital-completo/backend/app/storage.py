from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import boto3
import cloudinary
import cloudinary.uploader
from botocore.config import Config

from .config import settings


@dataclass(frozen=True)
class StoredObject:
    url: str
    path: str
    provider: str


class LocalStorage:
    provider = "local"

    def __init__(self) -> None:
        root = Path(settings.upload_dir)
        if not root.is_absolute():
            root = Path.cwd() / root
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: bytes, content_type: str, base_url: str) -> StoredObject:
        target = (self.root / key).resolve()
        if self.root not in target.parents:
            raise ValueError("Caminho de upload inválido")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        relative_url = f"/uploads/{key.replace('\\', '/')}"
        return StoredObject(
            url=f"{base_url.rstrip('/')}{relative_url}",
            path=relative_url,
            provider=self.provider,
        )


class S3CompatibleStorage:
    provider = "s3"

    def __init__(self) -> None:
        self.bucket = settings.s3_bucket_name or ""
        self.public_base_url = (settings.s3_public_base_url or "").rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region or "auto",
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
        )

    def save(self, key: str, data: bytes, content_type: str, base_url: str) -> StoredObject:
        del base_url
        normalized_key = key.replace("\\", "/").lstrip("/")
        self.client.put_object(
            Bucket=self.bucket,
            Key=normalized_key,
            Body=data,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable",
        )
        encoded_key = "/".join(quote(part, safe="") for part in normalized_key.split("/"))
        return StoredObject(
            url=f"{self.public_base_url}/{encoded_key}",
            path=normalized_key,
            provider=self.provider,
        )


class CloudinaryStorage:
    provider = "cloudinary"

    def __init__(self) -> None:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    def save(self, key: str, data: bytes, content_type: str, base_url: str) -> StoredObject:
        del base_url, content_type
        normalized_key = key.replace("\\", "/").lstrip("/")
        public_id = normalized_key.rsplit(".", 1)[0]

        result = cloudinary.uploader.upload(
            BytesIO(data),
            resource_type="image",
            public_id=public_id,
            format="webp",
            overwrite=False,
            unique_filename=False,
            use_filename=False,
            invalidate=False,
        )

        secure_url = result.get("secure_url")
        returned_public_id = result.get("public_id") or public_id
        if not secure_url:
            raise RuntimeError("Cloudinary não retornou uma URL segura para a imagem")

        return StoredObject(
            url=secure_url,
            path=returned_public_id,
            provider=self.provider,
        )


@lru_cache(maxsize=1)
def get_storage():
    provider = settings.storage_provider_normalized
    if provider == "s3":
        return S3CompatibleStorage()
    if provider == "cloudinary":
        return CloudinaryStorage()
    return LocalStorage()


def storage_health() -> dict:
    provider = settings.storage_provider_normalized
    if provider == "s3":
        configured = settings.s3_configuration_complete
        return {
            "provider": "s3",
            "persistent": configured,
            "configured": configured,
        }

    if provider == "cloudinary":
        configured = settings.cloudinary_configuration_complete
        return {
            "provider": "cloudinary",
            "persistent": configured,
            "configured": configured,
        }

    return {
        "provider": "local",
        "persistent": settings.environment.lower() != "production",
        "configured": True,
    }
