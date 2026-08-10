from __future__ import annotations

from fastapi import APIRouter

from rpf.api.deps import DbSession, PublishedEvent
from rpf.repositories import events as event_repo
from rpf.repositories import photos as photo_repo
from rpf.schemas.events import EventRead, EventWithCount

router = APIRouter(prefix="/v1/events", tags=["events"])


@router.get("", response_model=list[EventRead])
def list_events(db: DbSession) -> list[EventRead]:
    return [EventRead.model_validate(e) for e in event_repo.list_events(db, published_only=True)]


@router.get("/{slug}", response_model=EventWithCount)
def get_event(event: PublishedEvent, db: DbSession) -> EventWithCount:
    return EventWithCount(
        **EventRead.model_validate(event).model_dump(),
        photo_count=photo_repo.count_by_event(db, event.id),
    )
