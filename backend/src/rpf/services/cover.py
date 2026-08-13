"""Event cover images: an optional banner the frontend shows instead of its
slug-derived gradient placeholder.

Uploaded through the admin API only -- there is no UI for this yet. Covers
live in the public bucket alongside thumbs and previews (unlike originals,
they carry no payment concern, so a stable public URL is fine).
"""

from __future__ import annotations

import io
import re

from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from rpf.db.models import Event
from rpf.repositories import events as event_repo
from rpf.storage.base import StorageBackend, build_cover_key

MAX_COVER_BYTES = 5 * 1024 * 1024

_CONTENT_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
_EXTENSIONS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

# Matches the deterministic key built by build_cover_key(), so the previous
# object can be found for cleanup -- cover_url is the only place the key is
# recorded, there is no separate storage-key column.
_COVER_KEY_RE = re.compile(r"events/[^/]+/cover\.\w+")


class InvalidCoverImageError(Exception):
    """The uploaded file is not a jpg/png/webp image, or exceeds the size cap."""


def _validate(content: bytes) -> str:
    """Returns the Pillow format name (`"JPEG"`, `"PNG"`, `"WEBP"`).

    Checked against the decoded bytes, not the client-supplied content type --
    an upload endpoint cannot trust the label a browser or CLI happens to send.
    """
    if len(content) > MAX_COVER_BYTES:
        raise InvalidCoverImageError(
            f"Cover image is {len(content)} bytes, the limit is {MAX_COVER_BYTES}"
        )
    try:
        with Image.open(io.BytesIO(content)) as image:
            fmt = image.format
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidCoverImageError("File is not a valid image") from exc

    if fmt not in _EXTENSIONS:
        raise InvalidCoverImageError(f"Unsupported image format: {fmt or 'unknown'}")
    return fmt


def _existing_key(event: Event) -> str | None:
    if not event.cover_url:
        return None
    match = _COVER_KEY_RE.search(event.cover_url)
    return match.group(0) if match else None


def upload_cover(
    db: Session,
    *,
    event: Event,
    content: bytes,
    storage: StorageBackend,
) -> Event:
    fmt = _validate(content)
    ext = _EXTENSIONS[fmt]
    key = build_cover_key(event.slug, ext)
    previous_key = _existing_key(event)

    storage.put(key, io.BytesIO(content), content_type=_CONTENT_TYPES[fmt], visibility="public")
    # A re-upload in a different format leaves a stale key (cover.png ->
    # cover.jpg): clean it up so the old image doesn't linger in the bucket.
    if previous_key and previous_key != key:
        storage.delete(previous_key, visibility="public")

    cover_url = storage.url(key, visibility="public")
    return event_repo.set_cover_url(db, event, cover_url)


def delete_cover(db: Session, *, event: Event, storage: StorageBackend) -> Event:
    key = _existing_key(event)
    if key:
        storage.delete(key, visibility="public")
    return event_repo.set_cover_url(db, event, None)
