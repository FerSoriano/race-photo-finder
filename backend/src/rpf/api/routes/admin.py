"""Admin endpoints: event CRUD, stats, covers, and photo ingest.

Used by the `rpf` CLI (`upload`, `publish`) and by the `/admin` panel.
Guarded by X-Admin-Key. The server stays the only writer of the database and
object storage, so validation lives in exactly one place.
"""

from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import TypeAdapter, ValidationError

from rpf.api.deps import AdminGuard, AnyEvent, AppSettings, DbSession, Storage
from rpf.repositories import photos as photo_repo
from rpf.schemas.admin import AdminStats
from rpf.schemas.events import EventCreate, EventRead, EventUpdate, EventWithCount
from rpf.schemas.photos import BibIngest, PhotoIngestResult
from rpf.services import cover as cover_service
from rpf.services import events as events_service
from rpf.services import ingest as ingest_service
from rpf.services import stats as stats_service

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[AdminGuard])

_bibs_adapter = TypeAdapter(list[BibIngest])


@router.get("/stats", response_model=AdminStats)
def get_stats(db: DbSession) -> AdminStats:
    return stats_service.collect(db)


@router.get("/events", response_model=list[EventWithCount])
def list_events(db: DbSession) -> list[EventWithCount]:
    """Every event, published or draft -- the public route hides drafts."""
    return [
        EventWithCount(**EventRead.model_validate(event).model_dump(), photo_count=count)
        for event, count in events_service.list_with_counts(db)
    ]


@router.get("/events/{slug}", response_model=EventWithCount)
def get_event(event: AnyEvent, db: DbSession) -> EventWithCount:
    """Reaches a draft, unlike the public `GET /v1/events/{slug}` -- needed so
    the admin panel's edit page survives a reload on an unpublished event."""
    event, count = events_service.get_with_count(db, event)
    return EventWithCount(**EventRead.model_validate(event).model_dump(), photo_count=count)


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: DbSession) -> EventRead:
    try:
        event = events_service.create_event(db, **payload.model_dump())
    except events_service.EventSlugTakenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return EventRead.model_validate(event)


@router.patch("/events/{slug}", response_model=EventRead)
def update_event(event: AnyEvent, payload: EventUpdate, db: DbSession) -> EventRead:
    updated = events_service.update_event(db, event, **payload.model_dump(exclude_unset=True))
    return EventRead.model_validate(updated)


@router.delete("/events/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event: AnyEvent, db: DbSession, storage: Storage) -> Response:
    events_service.delete_event(db, event=event, storage=storage)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/events/{slug}/cover", response_model=EventRead)
async def upload_cover(
    event: AnyEvent,
    db: DbSession,
    storage: Storage,
    file: UploadFile = File(...),
) -> EventRead:
    content = await file.read()
    try:
        updated = cover_service.upload_cover(db, event=event, content=content, storage=storage)
    except cover_service.InvalidCoverImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return EventRead.model_validate(updated)


@router.delete("/events/{slug}/cover", response_model=EventRead)
def delete_cover(event: AnyEvent, db: DbSession, storage: Storage) -> EventRead:
    updated = cover_service.delete_cover(db, event=event, storage=storage)
    return EventRead.model_validate(updated)


@router.get("/events/{slug}/photos/hashes", response_model=list[str])
def list_ingested_hashes(event: AnyEvent, db: DbSession) -> list[str]:
    """Lets the CLI skip already-uploaded photos before sending any bytes."""
    return sorted(photo_repo.existing_sha256s(db, event.id))


@router.post(
    "/events/{slug}/photos",
    response_model=PhotoIngestResult,
    status_code=status.HTTP_201_CREATED,
)
async def upload_photo(
    event: AnyEvent,
    db: DbSession,
    storage: Storage,
    settings: AppSettings,
    file: UploadFile = File(...),
    sha256: str = Form(...),
    bibs: str = Form("[]", description='JSON array, e.g. [{"number":"19131"}]'),
    model_name: str | None = Form(None),
) -> PhotoIngestResult:
    content = await file.read()

    try:
        parsed_bibs = _bibs_adapter.validate_python(json.loads(bibs))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid bibs payload: {exc}",
        ) from exc

    # Verifying the client's hash keeps `sha256` trustworthy as the idempotency
    # key -- otherwise a truncated upload could claim an identity it does not have.
    actual = hashlib.sha256(content).hexdigest()
    if actual != sha256:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"sha256 mismatch: declared {sha256}, received {actual}",
        )

    photo, created = ingest_service.ingest_photo(
        db,
        event=event,
        filename=file.filename or "unnamed.jpg",
        content=content,
        sha256=sha256,
        bibs=parsed_bibs,
        storage=storage,
        settings=settings,
        model_name=model_name,
    )
    return PhotoIngestResult(id=photo.id, filename=photo.original_filename, created=created)
