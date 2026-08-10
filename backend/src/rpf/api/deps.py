"""Shared FastAPI dependencies."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy.orm import Session

from rpf.config import Settings, get_settings
from rpf.db.models import Event
from rpf.db.session import get_db
from rpf.repositories import events as event_repo
from rpf.storage.base import StorageBackend
from rpf.storage.factory import get_storage

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
Storage = Annotated[StorageBackend, Depends(get_storage)]


def require_admin(
    settings: AppSettings,
    x_admin_key: Annotated[str | None, Header()] = None,
) -> None:
    """Guards every /v1/admin route. Constant-time compare, no timing oracle."""
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing admin key"
        )


AdminGuard = Depends(require_admin)


def get_published_event(
    db: DbSession,
    slug: Annotated[str, Path()],
) -> Event:
    """Public lookup: unpublished events are indistinguishable from missing."""
    event = event_repo.get_by_slug(db, slug, published_only=True)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def get_any_event(db: DbSession, slug: Annotated[str, Path()]) -> Event:
    """Admin lookup: reaches unpublished events too."""
    event = event_repo.get_by_slug(db, slug)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


PublishedEvent = Annotated[Event, Depends(get_published_event)]
AnyEvent = Annotated[Event, Depends(get_any_event)]
