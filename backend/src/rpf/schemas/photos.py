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


class BibIngest(BaseModel):
    number: str = Field(max_length=16)
    is_uncertain: bool = False
    confidence: float | None = None


class PhotoIngestResult(BaseModel):
    id: uuid.UUID
    filename: str
    created: bool  # False when the sha256 was already present
