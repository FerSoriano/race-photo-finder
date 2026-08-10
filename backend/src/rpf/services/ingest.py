"""Ingest: turn an uploaded original into stored renditions + DB rows.

Shared by the admin API and (indirectly) the `rpf upload` CLI, so there is one
definition of what "a photo is in the system" means.
"""

from __future__ import annotations

import io

from sqlalchemy.orm import Session

from rpf.config import Settings
from rpf.db.models import Event, Photo
from rpf.detection.manifest import sha256_of  # noqa: F401  (re-exported for callers)
from rpf.repositories import photos as photo_repo
from rpf.schemas.photos import BibIngest
from rpf.services import derivatives as derivatives_service
from rpf.storage.base import StorageBackend, build_key


def ingest_photo(
    db: Session,
    *,
    event: Event,
    filename: str,
    content: bytes,
    sha256: str,
    bibs: list[BibIngest],
    storage: StorageBackend,
    settings: Settings,
    model_name: str | None = None,
) -> tuple[Photo, bool]:
    """Store one photo. Returns `(photo, created)`.

    Idempotent by `(event_id, sha256)`: re-uploading the same file is a no-op,
    which is what makes `rpf upload` safe to re-run after a dropped connection.
    """
    existing = photo_repo.get_by_sha256(db, event.id, sha256)
    if existing is not None:
        return existing, False

    rendition = derivatives_service.build(
        content,
        preview_max_px=settings.preview_max_px,
        thumb_max_px=settings.thumb_max_px,
        watermark_text=settings.watermark_text,
    )

    photo = photo_repo.create(
        db,
        event_id=event.id,
        original_filename=filename,
        sha256=sha256,
        # Keys are derived from the photo id, so they are stable and never
        # collide even when two events share a filename.
        storage_key_original="",
        storage_key_preview="",
        storage_key_thumb="",
        width=rendition.width,
        height=rendition.height,
        taken_at=rendition.taken_at,
    )

    photo_id = str(photo.id)
    photo.storage_key_original = build_key(event.slug, "original", photo_id)
    photo.storage_key_preview = build_key(event.slug, "preview", photo_id)
    photo.storage_key_thumb = build_key(event.slug, "thumb", photo_id)

    storage.put(photo.storage_key_original, io.BytesIO(content), visibility="private")
    storage.put(photo.storage_key_preview, io.BytesIO(rendition.preview), visibility="public")
    storage.put(photo.storage_key_thumb, io.BytesIO(rendition.thumb), visibility="public")

    photo_repo.add_bibs(
        db,
        photo,
        [(b.number, b.is_uncertain) for b in bibs],
        source="model",
        model_name=model_name,
    )

    db.flush()
    return photo, True
