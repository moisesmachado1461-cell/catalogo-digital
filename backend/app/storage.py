from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import boto3
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
        relative_url = f"/uploads/{key.replace('\\\\', '/')}"
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
        del base_url  # não é necessário no armazenamento externo
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


@lru_cache(maxsize=1)
def get_storage():
    if settings.storage_provider_normalized == "s3":
        return S3CompatibleStorage()
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

    return {
        "provider": "local",
        "persistent": settings.environment.lower() != "production",
        "configured": True,
    }
