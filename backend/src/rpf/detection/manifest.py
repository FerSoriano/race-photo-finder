"""The manifest file that carries detection results from the laptop to the API.

`rpf detect` writes it, `rpf upload` reads it. It is deliberately a plain JSON
file: it survives a crashed run, can be inspected and hand-corrected before
upload, and is the resume point when a race yields hundreds of photos.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from rpf.detection.base import Bib

MANIFEST_VERSION = 1
_CHUNK = 1024 * 1024


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class PhotoEntry:
    filename: str
    sha256: str
    bibs: list[Bib] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "sha256": self.sha256,
            "bibs": [asdict(b) for b in self.bibs],
            **({"error": self.error} if self.error else {}),
        }

    @classmethod
    def from_dict(cls, data: dict) -> PhotoEntry:
        return cls(
            filename=data["filename"],
            sha256=data["sha256"],
            bibs=[Bib(**b) for b in data.get("bibs", [])],
            error=data.get("error"),
        )


@dataclass
class Manifest:
    event_slug: str
    model: str
    photos: list[PhotoEntry] = field(default_factory=list)
    version: int = MANIFEST_VERSION
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def processed_filenames(self) -> set[str]:
        """Entries already done -- errored ones are retried on the next run."""
        return {p.filename for p in self.photos if p.error is None}

    def add(self, entry: PhotoEntry) -> None:
        self.photos = [p for p in self.photos if p.filename != entry.filename]
        self.photos.append(entry)

    def save(self, path: Path) -> None:
        self.generated_at = datetime.now(UTC).isoformat()
        payload = {
            "version": self.version,
            "event_slug": self.event_slug,
            "model": self.model,
            "generated_at": self.generated_at,
            "photos": [p.to_dict() for p in self.photos],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Manifest:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            event_slug=data["event_slug"],
            model=data.get("model", "unknown"),
            version=data.get("version", MANIFEST_VERSION),
            generated_at=data.get("generated_at", ""),
            photos=[PhotoEntry.from_dict(p) for p in data.get("photos", [])],
        )

    @classmethod
    def load_or_new(cls, path: Path, *, event_slug: str, model: str) -> Manifest:
        if path.is_file():
            manifest = cls.load(path)
            if manifest.event_slug != event_slug:
                raise ValueError(
                    f"{path} belongs to event {manifest.event_slug!r}, not {event_slug!r}"
                )
            manifest.model = model
            return manifest
        return cls(event_slug=event_slug, model=model)
