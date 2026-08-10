"""Data access for events. No HTTP concepts here."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
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
