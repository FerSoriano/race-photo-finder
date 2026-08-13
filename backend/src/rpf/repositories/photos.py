"""Data access for photos and their detected bib numbers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from rpf.db.models import Photo, PhotoBib


def get_by_sha256(db: Session, event_id: uuid.UUID, sha256: str) -> Photo | None:
    stmt = select(Photo).where(Photo.event_id == event_id, Photo.sha256 == sha256)
    return db.execute(stmt).scalar_one_or_none()


def get_in_event(db: Session, event_id: uuid.UUID, photo_id: uuid.UUID) -> Photo | None:
    """Fetch one photo, scoped to its event so ids cannot be used across events."""
    stmt = select(Photo).where(Photo.event_id == event_id, Photo.id == photo_id)
    return db.execute(stmt).scalar_one_or_none()


def list_by_ids(db: Session, event_id: uuid.UUID, photo_ids: Sequence[uuid.UUID]) -> list[Photo]:
    """Fetch several photos of one event. Ids that do not match are absent.

    The `event_id` filter belongs in the query, not in a comprehension over the
    result: it is what stops an id from another event being resolved at all.
    """
    if not photo_ids:
        return []
    stmt = select(Photo).where(Photo.event_id == event_id, Photo.id.in_(photo_ids))
    return list(db.execute(stmt).scalars())


def existing_sha256s(db: Session, event_id: uuid.UUID) -> set[str]:
    """Used by `rpf upload` to skip photos already ingested."""
    stmt = select(Photo.sha256).where(Photo.event_id == event_id)
    return set(db.execute(stmt).scalars())


def create(
    db: Session,
    *,
    event_id: uuid.UUID,
    original_filename: str,
    sha256: str,
    storage_key_original: str,
    storage_key_preview: str,
    storage_key_thumb: str,
    width: int | None = None,
    height: int | None = None,
    taken_at: datetime | None = None,
) -> Photo:
    photo = Photo(
        event_id=event_id,
        original_filename=original_filename,
        sha256=sha256,
        storage_key_original=storage_key_original,
        storage_key_preview=storage_key_preview,
        storage_key_thumb=storage_key_thumb,
        width=width,
        height=height,
        taken_at=taken_at,
    )
    db.add(photo)
    db.flush()
    return photo


def add_bibs(
    db: Session,
    photo: Photo,
    bibs: list[tuple[str, bool]],
    *,
    source: str = "model",
    model_name: str | None = None,
) -> None:
    """Attach `(bib_number, is_uncertain)` pairs to a photo."""
    for number, uncertain in bibs:
        db.add(
            PhotoBib(
                photo_id=photo.id,
                event_id=photo.event_id,
                bib_number=number,
                is_uncertain=uncertain,
                source=source,
                model_name=model_name,
            )
        )
    db.flush()


def search_by_bib(
    db: Session,
    event_id: uuid.UUID,
    bib: str,
    *,
    limit: int = 200,
    offset: int = 0,
) -> list[Photo]:
    """Exact-match search. Single seek on ix_photo_bibs_event_bib."""
    stmt = (
        select(Photo)
        .join(PhotoBib, PhotoBib.photo_id == Photo.id)
        .where(PhotoBib.event_id == event_id, PhotoBib.bib_number == bib)
        .options(selectinload(Photo.bibs))
        .order_by(Photo.taken_at.asc().nullslast(), Photo.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).unique().scalars())


# Trigram similarity is low for short numeric strings: one wrong digit in a
# 5-digit bib scores 0.333 (19131 vs 19181), which is exactly the case we want
# to catch. 0.3 admits those while still rejecting unrelated numbers, which
# score below 0.15 in practice.
SIMILARITY_THRESHOLD = 0.3


def search_similar_bibs(
    db: Session,
    event_id: uuid.UUID,
    bib: str,
    *,
    limit: int = 20,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[str]:
    """Fallback for OCR near-misses (a 6 read as an 8, a dropped digit).

    Returns candidate bib numbers, not photos, so the UI can ask "did you mean
    19131?" instead of silently showing someone else's photos.

    Uses the `%` operator rather than `similarity() > x` because only `%` can
    be answered by ix_photo_bibs_number_trgm. Its cutoff is a GUC, so it is set
    transaction-locally -- a session-wide set_limit() would leak into unrelated
    requests through the connection pool.
    """
    db.execute(
        text("SELECT set_config('pg_trgm.similarity_threshold', :t, true)"),
        {"t": str(threshold)},
    )

    score = func.similarity(PhotoBib.bib_number, bib)
    stmt = (
        select(PhotoBib.bib_number)
        .where(
            PhotoBib.event_id == event_id,
            PhotoBib.bib_number != bib,
            PhotoBib.bib_number.op("%")(bib),
        )
        .group_by(PhotoBib.bib_number)
        .order_by(func.max(score).desc(), PhotoBib.bib_number)
        .limit(limit)
    )
    return [row[0] for row in db.execute(stmt)]


def count_by_event(db: Session, event_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Photo).where(Photo.event_id == event_id)
    return db.execute(stmt).scalar_one()


def count_all(db: Session) -> int:
    return db.execute(select(func.count()).select_from(Photo)).scalar_one()


def counts_by_event(db: Session) -> dict[uuid.UUID, int]:
    """One grouped query instead of one `count_by_event` call per event.

    Events with zero photos are absent from the result -- callers must use
    `.get(event_id, 0)`, not index into this dict directly.
    """
    stmt = select(Photo.event_id, func.count()).group_by(Photo.event_id)
    return dict(db.execute(stmt).all())


def storage_keys_for_event(db: Session, event_id: uuid.UUID) -> list[tuple[str, str, str]]:
    """`(original, preview, thumb)` storage keys for every photo of an event.

    Selects columns, not ORM objects, so memory stays flat even on a
    many-thousand-photo event -- this exists only to feed a storage sweep
    before deleting the event.
    """
    stmt = select(
        Photo.storage_key_original, Photo.storage_key_preview, Photo.storage_key_thumb
    ).where(Photo.event_id == event_id)
    return [tuple(row) for row in db.execute(stmt).all()]
