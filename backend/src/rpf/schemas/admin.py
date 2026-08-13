from __future__ import annotations

from pydantic import BaseModel


class AdminStats(BaseModel):
    """Dashboard totals. `events_total` is redundant with the sum of the two
    split counts, but it is the number the dashboard headline shows, and
    computing it client-side invites drift."""

    events_total: int
    events_published: int
    events_draft: int
    photos_total: int
