from __future__ import annotations

from pathlib import Path

import pytest

from rpf.detection.base import Bib
from rpf.detection.manifest import Manifest, PhotoEntry, sha256_of


def _manifest() -> Manifest:
    return Manifest(
        event_slug="21k-gdl-2026",
        model="qwen2.5vl:7b",
        photos=[
            PhotoEntry(
                filename="21k-gdl-3.jpg",
                sha256="abc",
                bibs=[Bib("19131"), Bib("6133"), Bib("13441")],
            )
        ],
    )


def test_roundtrip(tmp_path: Path):
    path = tmp_path / "manifest.json"
    _manifest().save(path)
    loaded = Manifest.load(path)

    assert loaded.event_slug == "21k-gdl-2026"
    assert [b.number for b in loaded.photos[0].bibs] == ["19131", "6133", "13441"]


def test_uncertain_flag_survives_roundtrip(tmp_path: Path):
    path = tmp_path / "manifest.json"
    manifest = Manifest(event_slug="e", model="m")
    manifest.add(PhotoEntry(filename="a.jpg", sha256="x", bibs=[Bib("234", is_uncertain=True)]))
    manifest.save(path)

    assert Manifest.load(path).photos[0].bibs[0].is_uncertain is True


def test_add_replaces_existing_entry(tmp_path: Path):
    manifest = Manifest(event_slug="e", model="m")
    manifest.add(PhotoEntry(filename="a.jpg", sha256="1"))
    manifest.add(PhotoEntry(filename="a.jpg", sha256="2"))

    assert len(manifest.photos) == 1
    assert manifest.photos[0].sha256 == "2"


def test_errored_photos_are_retried():
    """A failed photo must not count as processed, or a crash would lose it."""
    manifest = Manifest(event_slug="e", model="m")
    manifest.add(PhotoEntry(filename="ok.jpg", sha256="1"))
    manifest.add(PhotoEntry(filename="bad.jpg", sha256="", error="ollama timeout"))

    assert manifest.processed_filenames == {"ok.jpg"}


def test_load_or_new_rejects_a_different_event(tmp_path: Path):
    path = tmp_path / "manifest.json"
    _manifest().save(path)

    with pytest.raises(ValueError, match="belongs to event"):
        Manifest.load_or_new(path, event_slug="other-race", model="m")


def test_load_or_new_creates_when_absent(tmp_path: Path):
    manifest = Manifest.load_or_new(tmp_path / "none.json", event_slug="e", model="m")
    assert manifest.photos == []


def test_sha256_of(tmp_path: Path):
    path = tmp_path / "f.bin"
    path.write_bytes(b"hello")
    assert sha256_of(path) == ("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")
