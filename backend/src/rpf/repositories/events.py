"""Data access for events. No HTTP concepts here."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from rpf.db.models import Event


def get_by_slug(db: Session, slug: str, *, published_only: bool = False) -> Event | None:
    stmt = select(Event).where(Event.slug == slug)
    if published_only:
        stmt = stmt.where(Event.is_published.is_(True))
    return db.execute(stmt).scalar_one_or_none()


def get_by_id(db: Session, event_id: uuid.UUID) -> Event | None:
    return db.get(Event, event_id)


def list_events(db: Session, *, published_only: bool = True) -> list[Event]:
    stmt = select(Event)
    if published_only:
        stmt = stmt.where(Event.is_published.is_(True))
    stmt = stmt.order_by(Event.event_date.desc().nullslast(), Event.created_at.desc())
    return list(db.execute(stmt).scalars())


def create(
    db: Session,
    *,
    slug: str,
    name: str,
    event_date: date | None = None,
    location: str | None = None,
    description: str | None = None,
    is_published: bool = False,
) -> Event:
    event = Event(
        slug=slug,
        name=name,
        event_date=event_date,
        location=location,
        description=description,
        is_published=is_published,
    )
    db.add(event)
    db.flush()
    return event


def update(db: Session, event: Event, **fields: object) -> Event:
    """Sets only the fields passed in -- callers filter with `exclude_unset`,
    so a field left out of the request is left untouched, not reset to None."""
    for key, value in fields.items():
        setattr(event, key, value)
    db.flush()
    return event


def set_cover_url(db: Session, event: Event, cover_url: str | None) -> Event:
    event.cover_url = cover_url
    db.flush()
    return event


def count_by_published(db: Session) -> dict[bool, int]:
    """`{True: <published count>, False: <draft count>}`. A key can be absent
    if there are zero events in that state -- callers use `.get(key, 0)`."""
    stmt = select(Event.is_published, func.count()).group_by(Event.is_published)
    return dict(db.execute(stmt).all())


def delete(db: Session, event: Event) -> None:
    """A Core `DELETE`, not `db.delete(event)`.

    `Event.photos` is `cascade="all, delete-orphan"` without
    `passive_deletes=True`, so the ORM path would load every `Photo` and
    `PhotoBib` into the session and emit one statement per row. This lets
    Postgres apply the `ON DELETE CASCADE` already declared on those tables in
    a single statement.
    """
    db.execute(sa_delete(Event).where(Event.id == event.id))
    db.expunge(event)
