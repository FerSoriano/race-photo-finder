"""Application settings, loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["dev", "test", "prod"] = "dev"
    api_base_url: str = "http://localhost:8000"

    # Guards every /v1/admin route and the `rpf upload` CLI.
    admin_api_key: str = "dev-insecure-key"

    database_url: str = "postgresql+psycopg://rpf:rpf@localhost:5433/rpf"

    # --- Storage -------------------------------------------------------
    # "local" writes to LOCAL_STORAGE_ROOT; "s3" talks to any S3-compatible
    # provider (Cloudflare R2 in production, MinIO in docker compose).
    storage_backend: Literal["local", "s3"] = "local"
    local_storage_root: Path = BACKEND_ROOT / "var" / "storage"

    s3_endpoint_url: str | None = None
    s3_region: str = "auto"  # Cloudflare R2 requires the literal "auto"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    # Two buckets, because public access on R2 is granted per bucket (a custom
    # domain exposes the whole bucket) -- there is no per-prefix switch. Keeping
    # originals in their own private bucket is what makes paid downloads
    # enforceable: the only way to reach one is a signed URL we issue.
    s3_bucket: str = "race-photos-private"  # originals
    s3_public_bucket: str = "race-photos-public"  # thumbs + previews

    # CDN origin for the public bucket (R2 custom domain). Without it, public
    # objects fall back to signed URLs, which still work but bypass the CDN.
    s3_public_base_url: str | None = None
    # Lifetime of presigned URLs for private originals.
    presign_expires_seconds: int = 3600
    # Cap on photos per bulk-download request. Each one mints a signed URL, so
    # the cost is per-URL rather than per-byte -- but an uncapped list would be
    # a free way to ask the API to sign an entire event.
    max_bulk_download: int = 10

    # --- Image derivatives ---------------------------------------------
    thumb_max_px: int = 400
    preview_max_px: int = 1600
    watermark_text: str = "race-photo-finder"

    # --- Detection ------------------------------------------------------
    ollama_model: str = "qwen2.5vl:7b"
    ollama_host: str | None = None

    @model_validator(mode="after")
    def _check_production_safety(self) -> Settings:
        """Catch deployment mistakes at boot, not in production traffic."""
        if self.environment != "prod":
            return self

        if self.storage_backend == "local":
            raise ValueError(
                "STORAGE_BACKEND=local is not allowed in production: container "
                "filesystems are ephemeral, so every photo would be lost on the "
                "next deploy. Set STORAGE_BACKEND=s3 with R2 credentials."
            )
        if self.admin_api_key == Settings.model_fields["admin_api_key"].default:
            raise ValueError(
                "ADMIN_API_KEY is still the development default. Set a real "
                "secret -- it is the only thing guarding photo ingest."
            )
        if self.s3_public_bucket == self.s3_bucket:
            raise ValueError(
                "S3_BUCKET and S3_PUBLIC_BUCKET must differ: originals live in "
                "the private bucket, and a shared bucket would make them "
                "publicly downloadable."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
