"""SQLAlchemy models.

Search performance note: the hot query is "give me every photo of event X that
contains bib N". `photo_bibs` carries a denormalised `event_id` precisely so
that query is a single index seek on `ix_photo_bibs_event_bib` -- no join, no
scan. That is why this project does not need a native search extension.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Public URL of the cover image, or None to fall back to the frontend's
    # slug-derived gradient placeholder.
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Unpublished events are invisible to the public API but can be ingested
    # into, so photos can be uploaded before the announcement goes out.
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    photos: Mapped[list[Photo]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"
    __table_args__ = (
        # Makes re-running `rpf upload` idempotent.
        UniqueConstraint("event_id", "sha256", name="uq_photos_event_sha256"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))

    storage_key_original: Mapped[str] = mapped_column(String(500))
    storage_key_preview: Mapped[str] = mapped_column(String(500))
    storage_key_thumb: Mapped[str] = mapped_column(String(500))

    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped[Event] = relationship(back_populates="photos")
    bibs: Mapped[list[PhotoBib]] = relationship(
        back_populates="photo", cascade="all, delete-orphan"
    )


class PhotoBib(Base):
    """One bib number detected in one photo."""

    __tablename__ = "photo_bibs"
    __table_args__ = (
        UniqueConstraint("photo_id", "bib_number", name="uq_photo_bibs_photo_number"),
        Index("ix_photo_bibs_event_bib", "event_id", "bib_number"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    photo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"), index=True
    )
    # Denormalised from photos.event_id to keep the search query index-only.
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))

    bib_number: Mapped[str] = mapped_column(String(16))
    # True when the model flagged a digit it was unsure about (the "?234" case).
    is_uncertain: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="model")  # "model" | "manual"
    model_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    photo: Mapped[Photo] = relationship(back_populates="bibs")
