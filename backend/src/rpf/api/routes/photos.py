from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from rpf.api.deps import DbSession, PublishedEvent, Storage
from rpf.db.models import Photo
from rpf.schemas.photos import PhotoSearchResult
from rpf.services import search as search_service

router = APIRouter(prefix="/v1/events/{slug}", tags=["photos"])


@router.get("/photos", response_model=PhotoSearchResult)
def search_photos(
    event: PublishedEvent,
    db: DbSession,
    storage: Storage,
    bib: str = Query(min_length=1, max_length=16, description="Runner bib number"),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> PhotoSearchResult:
    """The core search. Backed by ix_photo_bibs_event_bib -- a single seek."""
    return search_service.search(db, event, bib, storage, limit=limit, offset=offset)


@router.get("/photos/{photo_id}/download")
def download_original(
    event: PublishedEvent,
    photo_id: uuid.UUID,
    db: DbSession,
    storage: Storage,
) -> RedirectResponse:
    """Redirects to a short-lived signed URL for the private original.

    Free and unlimited for now. This is the single choke point where the future
    payment check goes -- everything else stays untouched.
    """
    photo = db.get(Photo, photo_id)
    if photo is None or photo.event_id != event.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return RedirectResponse(url=storage.url(photo.storage_key_original, visibility="private"))
