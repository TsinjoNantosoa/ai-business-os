from __future__ import annotations

import secrets
from pathlib import Path

from app.core.config import settings


class StorageService:
    """Local filesystem storage with optional S3/MinIO backend."""

    def __init__(self) -> None:
        self._root = Path(settings.storage_local_path).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._s3 = None
        if settings.s3_endpoint_url and settings.s3_access_key and settings.s3_secret_key:
            try:
                import boto3

                self._s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.s3_endpoint_url,
                    aws_access_key_id=settings.s3_access_key,
                    aws_secret_access_key=settings.s3_secret_key,
                    region_name=settings.s3_region,
                )
            except ImportError:
                self._s3 = None

    @property
    def backend(self) -> str:
        return "s3" if self._s3 else "local"

    def build_key(self, org_id: str, filename: str) -> str:
        safe_name = Path(filename).name.replace(" ", "_")
        return f"{org_id}/{secrets.token_hex(8)}_{safe_name}"

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        if self._s3:
            extra = {"ContentType": content_type} if content_type else {}
            self._s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=data, **extra)
            return key

        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def read(self, key: str) -> bytes:
        if self._s3:
            response = self._s3.get_object(Bucket=settings.s3_bucket, Key=key)
            return response["Body"].read()

        path = self._root / key
        if not path.exists():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        if self._s3:
            self._s3.delete_object(Bucket=settings.s3_bucket, Key=key)
            return
        path = self._root / key
        if path.exists():
            path.unlink()
