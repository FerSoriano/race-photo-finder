"""The core product operation: find a runner's photos by bib number."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from rpf.db.models import Event, Photo
from rpf.repositories import photos as photo_repo
from rpf.schemas.photos import BibRead, PhotoRead, PhotoSearchResult
from rpf.storage.base import StorageBackend

_NON_DIGITS = re.compile(r"\D")


def normalize_query(bib: str) -> str:
    """Runners type "#1234", "1234 " or "n1234" -- accept all of them."""
    return _NON_DIGITS.sub("", bib.strip())


def to_read_model(photo: Photo, storage: StorageBackend) -> PhotoRead:
    return PhotoRead(
        id=photo.id,
        filename=photo.original_filename,
        thumb_url=storage.url(photo.storage_key_thumb, visibility="public"),
        preview_url=storage.url(photo.storage_key_preview, visibility="public"),
        width=photo.width,
        height=photo.height,
        taken_at=photo.taken_at,
        bibs=[BibRead(number=b.bib_number, is_uncertain=b.is_uncertain) for b in photo.bibs],
    )


def search(
    db: Session,
    event: Event,
    bib: str,
    storage: StorageBackend,
    *,
    limit: int = 200,
    offset: int = 0,
) -> PhotoSearchResult:
    normalized = normalize_query(bib)
    if not normalized:
        return PhotoSearchResult(event_slug=event.slug, bib=bib, total=0, photos=[])

    found = photo_repo.search_by_bib(db, event.id, normalized, limit=limit, offset=offset)

    similar: list[str] = []
    if not found:
        similar = photo_repo.search_similar_bibs(db, event.id, normalized)

    return PhotoSearchResult(
        event_slug=event.slug,
        bib=normalized,
        total=len(found),
        photos=[to_read_model(p, storage) for p in found],
        similar_bibs=similar,
    )
