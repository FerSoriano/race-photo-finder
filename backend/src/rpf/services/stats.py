"""Aggregate counts for the admin dashboard."""

from __future__ import annotations

from sqlalchemy.orm import Session

from rpf.repositories import events as event_repo
from rpf.repositories import photos as photo_repo
from rpf.schemas.admin import AdminStats


def collect(db: Session) -> AdminStats:
    by_published = event_repo.count_by_published(db)
    published = by_published.get(True, 0)
    draft = by_published.get(False, 0)
    return AdminStats(
        events_total=published + draft,
        events_published=published,
        events_draft=draft,
        photos_total=photo_repo.count_all(db),
    )
