"""Builds the configured StorageBackend. The single place that knows which
implementation is active."""

from __future__ import annotations

from functools import lru_cache

from rpf.config import Settings, get_settings
from rpf.storage.base import StorageBackend
from rpf.storage.local import LocalStorage
from rpf.storage.s3 import S3Storage


def build_storage(settings: Settings) -> StorageBackend:
    if settings.storage_backend == "local":
        return LocalStorage(
            root=settings.local_storage_root,
            public_base_url=settings.api_base_url,
        )
    return S3Storage(
        bucket=settings.s3_bucket,
        public_bucket=settings.s3_public_bucket,
        endpoint_url=settings.s3_endpoint_url,
        region=settings.s3_region,
        access_key_id=settings.s3_access_key_id,
        secret_access_key=settings.s3_secret_access_key,
        public_base_url=settings.s3_public_base_url,
        presign_expires_seconds=settings.presign_expires_seconds,
    )


@lru_cache
def get_storage() -> StorageBackend:
    return build_storage(get_settings())
