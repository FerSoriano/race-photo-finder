"""Handing out access to private originals.

Every download in the product passes through this module -- the single-photo
redirect and the bulk link list both end in `link_for`. That is deliberate:
originals live in a private bucket and a signed URL is the only way to reach
one, so this is the one place a future payment check has to be added. Keep it
that way; a second path to a signed original is a second place to forget.

The bytes never touch the API. We mint URLs and the browser fetches straight
from object storage, which is why a bulk download costs one query and no
bandwidth.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from rpf.config import Settings
from rpf.db.models import Event, Photo
from rpf.repositories import photos as photo_repo
from rpf.schemas.photos import BulkDownloadResult, PhotoDownloadLink
from rpf.storage.base import StorageBackend


class TooManyPhotosError(Exception):
    """More photos were requested in one call than the configured cap allows."""

    def __init__(self, requested: int, limit: int) -> None:
        self.requested = requested
        self.limit = limit
        super().__init__(f"Requested {requested} photos, the limit is {limit} per request")


class PhotosNotFoundError(Exception):
    """One or more requested ids do not name a photo of this event."""

    def __init__(self, missing: Sequence[uuid.UUID]) -> None:
        self.missing = list(missing)
        super().__init__("Photos not found: " + ", ".join(str(i) for i in self.missing))


def plan_download(photo_ids: Sequence[uuid.UUID], settings: Settings) -> list[uuid.UUID]:
    """De-duplicate the request and enforce the cap. No DB, no storage.

    De-duplication happens first, so a UI that sends the same photo twice is not
    punished for it. Order is preserved: the response pairs up with the rows the
    runner ticked.
    """
    unique = list(dict.fromkeys(photo_ids))
    if len(unique) > settings.max_bulk_download:
        raise TooManyPhotosError(len(unique), settings.max_bulk_download)
    return unique


def link_for(photo: Photo, storage: StorageBackend) -> PhotoDownloadLink:
    """Mint one signed URL for a photo's original.

    Free and unlimited for now -- this is where the future payment check goes.
    """
    return PhotoDownloadLink(
        id=photo.id,
        filename=photo.original_filename,
        url=storage.url(
            photo.storage_key_original,
            visibility="private",
            # Keys are named after the photo id; without this the runner saves
            # a UUID instead of the photo.
            download_filename=photo.original_filename,
        ),
    )


def link_for_id(
    db: Session,
    event: Event,
    photo_id: uuid.UUID,
    storage: StorageBackend,
) -> PhotoDownloadLink:
    """Look up one photo of `event` and mint its link. Raises `PhotosNotFoundError`."""
    photo = photo_repo.get_in_event(db, event.id, photo_id)
    if photo is None:
        raise PhotosNotFoundError([photo_id])
    return link_for(photo, storage)


def build_links(
    db: Session,
    event: Event,
    photo_ids: Sequence[uuid.UUID],
    storage: StorageBackend,
    settings: Settings,
) -> BulkDownloadResult:
    """Mint links for a selection of photos, or fail the whole request.

    An unknown id is an error rather than a silent omission: a stale gallery
    selection should surface as a message, not as a download that quietly comes
    up short.
    """
    wanted = plan_download(photo_ids, settings)

    found = {photo.id: photo for photo in photo_repo.list_by_ids(db, event.id, wanted)}
    missing = [photo_id for photo_id in wanted if photo_id not in found]
    if missing:
        raise PhotosNotFoundError(missing)

    return BulkDownloadResult(
        event_slug=event.slug,
        expires_in=settings.presign_expires_seconds,
        photos=[link_for(found[photo_id], storage) for photo_id in wanted],
    )
