"""Admin ingest endpoints, used by the `rpf upload` CLI.

Guarded by X-Admin-Key. The server stays the only writer of the database and
object storage, so validation lives in exactly one place.
"""

from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import TypeAdapter, ValidationError

from rpf.api.deps import AdminGuard, AnyEvent, AppSettings, DbSession, Storage
from rpf.repositories import events as event_repo
from rpf.repositories import photos as photo_repo
from rpf.schemas.events import EventCreate, EventRead
from rpf.schemas.photos import BibIngest, PhotoIngestResult
from rpf.services import ingest as ingest_service

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[AdminGuard])

_bibs_adapter = TypeAdapter(list[BibIngest])


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: DbSession) -> EventRead:
    if event_repo.get_by_slug(db, payload.slug) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event {payload.slug!r} already exists",
        )
    event = event_repo.create(db, **payload.model_dump())
    return EventRead.model_validate(event)


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
