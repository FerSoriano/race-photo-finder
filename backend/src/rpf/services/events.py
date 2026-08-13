"""Event CRUD for the admin API.

`create_event` and `update_event` used to live inline in
`api/routes/admin.py`, calling `event_repo` directly -- a shortcut the layering
rule in `backend/CLAUDE.md` does not allow. They move here alongside
`delete_event`, which has no honest home outside a service: it orchestrates
both the events repository and `StorageBackend`, and a route may not call
storage directly.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from rpf.db.models import Event
from rpf.repositories import events as event_repo
from rpf.repositories import photos as photo_repo
from rpf.services import cover as cover_service
from rpf.storage.base import StorageBackend


class EventSlugTakenError(Exception):
    """An event with this slug already exists."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Event {slug!r} already exists")


def create_event(
    db: Session,
    *,
    slug: str,
    name: str,
    event_date: date | None = None,
    location: str | None = None,
    description: str | None = None,
    is_published: bool = False,
) -> Event:
    if event_repo.get_by_slug(db, slug) is not None:
        raise EventSlugTakenError(slug)
    return event_repo.create(
        db,
        slug=slug,
        name=name,
        event_date=event_date,
        location=location,
        description=description,
        is_published=is_published,
    )


def update_event(db: Session, event: Event, **fields: object) -> Event:
    """Sets only the fields passed in -- the route filters with `exclude_unset`
    so a field left out of the request stays untouched."""
    return event_repo.update(db, event, **fields)


def get_with_count(db: Session, event: Event) -> tuple[Event, int]:
    return event, photo_repo.count_by_event(db, event.id)


def list_with_counts(db: Session) -> list[tuple[Event, int]]:
    """Every event, published or not, paired with its photo count.

    One grouped query (`counts_by_event`) rather than one `count_by_event` call
    per event -- N+1 round trips for a 200-event catalogue is exactly the kind
    of thing this project avoids elsewhere (see the bib search's single seek).
    """
    events = event_repo.list_events(db, published_only=False)
    counts = photo_repo.counts_by_event(db)
    return [(event, counts.get(event.id, 0)) for event in events]


def delete_event(db: Session, *, event: Event, storage: StorageBackend) -> int:
    """Delete an event, its photos, and every object those photos own.

    Returns the number of photos deleted, for the caller to log or report.

    Storage first, database second. Neither order is transactional and there
    is no reconciliation job, so the choice is between two failure modes:

    - Storage first (this order): a sweep that raises leaves the DB row and
      its photos intact, and the delete is simply retryable.
    - Database first: a commit failing *after* the objects are gone would
      leave a live, possibly published event with 404ing thumbnails and
      nothing pointing at why.

    This matches the existing precedent in `services/cover.py::upload_cover`,
    which also mutates storage before the row. Note `db/session.py::get_db`
    commits only after the route returns, so this function's own `flush()`
    is not itself durable -- the route is what makes the delete final.
    """
    keys = photo_repo.storage_keys_for_event(db, event.id)
    photo_count = len(keys)

    private_keys = [original for original, _preview, _thumb in keys]
    public_keys = [key for _original, preview, thumb in keys for key in (preview, thumb)]
    cover = cover_service.cover_key(event)
    if cover:
        public_keys.append(cover)

    if private_keys:
        storage.delete_many(private_keys, visibility="private")
    if public_keys:
        storage.delete_many(public_keys, visibility="public")

    event_repo.delete(db, event)
    return photo_count
