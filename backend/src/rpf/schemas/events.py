from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)
    name: str = Field(max_length=200)
    event_date: date | None = None
    location: str | None = Field(default=None, max_length=200)
    description: str | None = None
    is_published: bool = False


class EventUpdate(BaseModel):
    """Partial update. The slug is the path identifier and is immutable here --
    changing it would break any link already shared for the event."""

    name: str | None = Field(default=None, max_length=200)
    event_date: date | None = None
    location: str | None = Field(default=None, max_length=200)
    description: str | None = None
    is_published: bool | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    event_date: date | None
    location: str | None
    description: str | None
    cover_url: str | None = None
    is_published: bool


class EventWithCount(EventRead):
    photo_count: int
