"""Storage abstraction.

The rest of the codebase talks to object storage **only** through
`StorageBackend`. Nothing outside `rpf.storage` may import boto3, reference a
bucket name, or build a URL by hand -- that is what lets us swap Cloudflare R2
for B2, S3 or plain disk by editing .env instead of code.
"""

from __future__ import annotations

from typing import BinaryIO, Literal, Protocol, runtime_checkable

Visibility = Literal["public", "private"]

# Key layout, shared by every backend:
#   events/{event_slug}/{original|preview|thumb}/{photo_id}.jpg
Derivative = Literal["original", "preview", "thumb"]


def build_key(event_slug: str, derivative: Derivative, photo_id: str, ext: str = "jpg") -> str:
    return f"events/{event_slug}/{derivative}/{photo_id}.{ext}"


def build_cover_key(event_slug: str, ext: str) -> str:
    return f"events/{event_slug}/cover.{ext}"


@runtime_checkable
class StorageBackend(Protocol):
    """Minimal object-storage surface the application depends on."""

    def put(
        self,
        key: str,
        data: BinaryIO,
        content_type: str = "image/jpeg",
        visibility: Visibility = "private",
    ) -> None:
        """Store `data` at `key`, overwriting any existing object."""
        ...

    def get(self, key: str, visibility: Visibility = "private") -> bytes:
        """Return the object's bytes. Raises `FileNotFoundError` if absent."""
        ...

    def url(
        self,
        key: str,
        visibility: Visibility = "private",
        download_filename: str | None = None,
    ) -> str:
        """Return a URL a browser can fetch.

        Public objects get a stable CDN URL; private ones get a short-lived
        signed URL.

        `download_filename` asks the browser to save the object under that name
        instead of the storage key's. Keys are named after the photo id, so
        without it a download lands as a UUID -- tolerable for one file, useless
        for ten.
        """
        ...

    def exists(self, key: str, visibility: Visibility = "private") -> bool: ...

    def delete(self, key: str, visibility: Visibility = "private") -> None:
        """Remove the object. Deleting a missing key is not an error."""
        ...
