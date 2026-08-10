"""Filesystem-backed storage for local development and tests."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from rpf.storage.base import Visibility


class LocalStorage:
    """Writes objects under `root`, served by the app's /media static mount.

    Visibility is accepted but not enforced: everything under the media mount
    is readable. This is a development-only convenience -- the public/private
    split is real only on the S3 backend, so test that boundary against MinIO,
    never against this one.
    """

    def __init__(self, root: Path, public_base_url: str) -> None:
        self._root = Path(root)
        self._public_base_url = public_base_url.rstrip("/")
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Guard against keys escaping the storage root via "..".
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root.resolve()):
            raise ValueError(f"key escapes storage root: {key!r}")
        return path

    def put(
        self,
        key: str,
        data: BinaryIO,
        content_type: str = "image/jpeg",
        visibility: Visibility = "private",
    ) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            shutil.copyfileobj(data, fh)

    def get(self, key: str, visibility: Visibility = "private") -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def url(self, key: str, visibility: Visibility = "private") -> str:
        return f"{self._public_base_url}/media/{key}"

    def exists(self, key: str, visibility: Visibility = "private") -> bool:
        return self._path(key).is_file()

    def delete(self, key: str, visibility: Visibility = "private") -> None:
        self._path(key).unlink(missing_ok=True)
