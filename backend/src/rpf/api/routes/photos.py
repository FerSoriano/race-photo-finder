from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from rpf.api.deps import AppSettings, DbSession, PublishedEvent, Storage
from rpf.schemas.photos import BulkDownloadRequest, BulkDownloadResult, PhotoSearchResult
from rpf.services import download as download_service
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
    """Redirects to a short-lived signed URL for the private original."""
    try:
        link = download_service.link_for_id(db, event, photo_id, storage)
    except download_service.PhotosNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        ) from exc
    return RedirectResponse(url=link.url)


@router.post("/photos/download", response_model=BulkDownloadResult)
def download_originals(
    event: PublishedEvent,
    payload: BulkDownloadRequest,
    db: DbSession,
    storage: Storage,
    settings: AppSettings,
) -> BulkDownloadResult:
    """Signed URLs for a selection of photos, so the gallery can offer
    "download the ones I ticked" in a single call.

    The photos are fetched straight from object storage by the browser -- the
    API only signs, so this stays cheap. Capped by MAX_BULK_DOWNLOAD.
    """
    try:
        return download_service.build_links(db, event, payload.photo_ids, storage, settings)
    except download_service.TooManyPhotosError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except download_service.PhotosNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
