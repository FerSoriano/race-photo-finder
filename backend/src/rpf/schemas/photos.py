from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BibRead(BaseModel):
    number: str
    is_uncertain: bool


class PhotoRead(BaseModel):
    """A photo as the public site sees it.

    Note what is absent: `storage_key_original`. The original is private and is
    only reachable through a separate, signed download endpoint.
    """

    id: uuid.UUID
    filename: str
    thumb_url: str
    preview_url: str
    width: int | None
    height: int | None
    taken_at: datetime | None
    bibs: list[BibRead]


class PhotoSearchResult(BaseModel):
    event_slug: str
    bib: str
    total: int
    photos: list[PhotoRead]
    # Populated only when `photos` is empty, so the UI can offer
    # "did you mean 19181?" instead of a dead end.
    similar_bibs: list[str] = Field(default_factory=list)


class BulkDownloadRequest(BaseModel):
    """The photos a runner ticked in the gallery.

    The upper bound is not declared here: it comes from
    `Settings.max_bulk_download`, which a schema cannot read, so the service
    enforces it.
    """

    photo_ids: list[uuid.UUID] = Field(min_length=1)


class PhotoDownloadLink(BaseModel):
    id: uuid.UUID
    filename: str
    # Short-lived and signed. The storage key it points at is never exposed.
    url: str


class BulkDownloadResult(BaseModel):
    event_slug: str
    expires_in: int  # seconds the links stay valid
    photos: list[PhotoDownloadLink]


class BibIngest(BaseModel):
    number: str = Field(max_length=16)
    is_uncertain: bool = False
    confidence: float | None = None


class PhotoIngestResult(BaseModel):
    id: uuid.UUID
    filename: str
    created: bool  # False when the sha256 was already present
