"""
Abstraccion de almacenamiento de archivos.
LocalStorage (dev) y S3Compatible (prod: MinIO, Cloudflare R2, AWS S3).
Cambia STORAGE_BACKEND en .env sin tocar el codigo.
"""
from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Guarda el archivo y retorna el storage_key."""
        ...

    @abstractmethod
    async def get_url(self, storage_key: str, expires_seconds: int = 3600) -> str:
        """Retorna URL temporal de descarga."""
        ...

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        ...

    @abstractmethod
    async def read(self, storage_key: str) -> bytes:
        ...


class LocalStorage(StorageBackend):
    """Almacenamiento local — para desarrollo."""

    def __init__(self, base_path: str) -> None:
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    async def save(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        ext = Path(filename).suffix
        key = f"{uuid.uuid4().hex}{ext}"
        (self.base / key).write_bytes(file_bytes)
        return key

    async def get_url(self, storage_key: str, expires_seconds: int = 3600) -> str:
        return f"/api/v1/files/{storage_key}"

    async def delete(self, storage_key: str) -> None:
        path = self.base / storage_key
        if path.exists():
            path.unlink()

    async def read(self, storage_key: str) -> bytes:
        return (self.base / storage_key).read_bytes()

    def local_path(self, storage_key: str) -> Path:
        return self.base / storage_key


class S3CompatibleStorage(StorageBackend):
    """
    Almacenamiento S3-compatible: MinIO self-hosted, Cloudflare R2, AWS S3.
    Configurar con S3_ENDPOINT_URL, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY.
    """

    def __init__(self) -> None:
        import boto3
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self.bucket = settings.s3_bucket

    async def save(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        import asyncio
        ext = Path(filename).suffix
        key = f"{uuid.uuid4().hex}{ext}"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.put_object(
                Bucket=self.bucket, Key=key,
                Body=file_bytes, ContentType=content_type,
            ),
        )
        return key

    async def get_url(self, storage_key: str, expires_seconds: int = 3600) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_key},
                ExpiresIn=expires_seconds,
            ),
        )

    async def delete(self, storage_key: str) -> None:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.delete_object(Bucket=self.bucket, Key=storage_key),
        )

    async def read(self, storage_key: str) -> bytes:
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.get_object(Bucket=self.bucket, Key=storage_key),
        )
        return response["Body"].read()


_storage: StorageBackend | None = None


def storage() -> StorageBackend:
    """Singleton lazy — retorna el backend configurado en STORAGE_BACKEND."""
    global _storage
    if _storage is None:
        if settings.storage_backend == "s3":
            _storage = S3CompatibleStorage()
        else:
            _storage = LocalStorage(settings.storage_local_path)
    return _storage
