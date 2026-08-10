"""Contract tests for the storage abstraction.

`test_local_satisfies_protocol` / `test_s3_satisfies_protocol` are the guard
rail for the swap-the-provider promise: any new backend must pass them.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from rpf.config import Settings
from rpf.storage.base import StorageBackend, build_key
from rpf.storage.factory import build_storage
from rpf.storage.local import LocalStorage
from rpf.storage.s3 import S3Storage


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(root=tmp_path, public_base_url="http://testserver")


def test_local_satisfies_protocol(storage):
    assert isinstance(storage, StorageBackend)


def test_s3_satisfies_protocol():
    assert isinstance(S3Storage(bucket="x", endpoint_url="http://localhost:9000"), StorageBackend)


class TestLocalStorage:
    def test_put_then_get(self, storage):
        storage.put("events/race/thumb/abc.jpg", io.BytesIO(b"data"))
        assert storage.get("events/race/thumb/abc.jpg") == b"data"

    def test_get_missing_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.get("nope.jpg")

    def test_exists(self, storage):
        assert storage.exists("a.jpg") is False
        storage.put("a.jpg", io.BytesIO(b"x"))
        assert storage.exists("a.jpg") is True

    def test_delete_is_idempotent(self, storage):
        storage.put("a.jpg", io.BytesIO(b"x"))
        storage.delete("a.jpg")
        storage.delete("a.jpg")  # must not raise
        assert storage.exists("a.jpg") is False

    def test_url_points_at_the_media_mount(self, storage):
        assert storage.url("events/race/thumb/a.jpg") == (
            "http://testserver/media/events/race/thumb/a.jpg"
        )

    def test_key_cannot_escape_the_root(self, storage):
        with pytest.raises(ValueError, match="escapes storage root"):
            storage.put("../../etc/passwd", io.BytesIO(b"x"))


class TestBuildKey:
    def test_layout(self):
        assert build_key("21k-gdl", "thumb", "abc-123") == "events/21k-gdl/thumb/abc-123.jpg"


class TestFactory:
    def test_local_selected_by_config(self, tmp_path):
        settings = Settings(storage_backend="local", local_storage_root=tmp_path)
        assert isinstance(build_storage(settings), LocalStorage)

    def test_s3_selected_by_config(self):
        settings = Settings(
            storage_backend="s3",
            s3_endpoint_url="https://acct.r2.cloudflarestorage.com",
            s3_region="auto",
            s3_access_key_id="k",
            s3_secret_access_key="s",
        )
        assert isinstance(build_storage(settings), S3Storage)

    def test_switching_provider_is_config_only(self, tmp_path):
        """Same call sites, different backend -- this is the whole point."""
        local = build_storage(Settings(storage_backend="local", local_storage_root=tmp_path))
        s3 = build_storage(Settings(storage_backend="s3", s3_endpoint_url="http://localhost:9000"))
        for backend in (local, s3):
            assert isinstance(backend, StorageBackend)


class TestBucketSeparation:
    """Originals must never land in the publicly readable bucket.

    On R2 public access is per bucket, so this routing is the only thing
    keeping originals unreachable without a signed URL -- and therefore the
    foundation of the future paid-download model.
    """

    def _storage(self, **kwargs) -> S3Storage:
        return S3Storage(
            bucket="private-bucket",
            public_bucket="public-bucket",
            endpoint_url="http://localhost:9000",
            **kwargs,
        )

    def test_private_objects_use_the_private_bucket(self):
        assert self._storage()._bucket_for("private") == "private-bucket"

    def test_public_objects_use_the_public_bucket(self):
        assert self._storage()._bucket_for("public") == "public-bucket"

    def test_defaults_to_private_when_no_public_bucket_is_configured(self):
        """Fail closed: a missing public bucket must not expose the private one."""
        storage = S3Storage(bucket="only-bucket", endpoint_url="http://localhost:9000")
        assert storage._bucket_for("public") == "only-bucket"

    def test_public_url_uses_the_cdn_domain(self):
        storage = self._storage(public_base_url="https://photos.example.com")
        assert storage.url("events/r/thumb/a.jpg", visibility="public") == (
            "https://photos.example.com/events/r/thumb/a.jpg"
        )

    def test_private_url_is_signed_and_expires(self):
        url = self._storage(access_key_id="k", secret_access_key="s").url(
            "events/r/original/a.jpg", visibility="private"
        )
        assert "X-Amz-Signature=" in url
        assert "X-Amz-Expires=" in url
        # A signed URL must point at the private bucket, never the public one.
        assert "private-bucket" in url

    def test_a_cdn_domain_never_leaks_originals(self):
        """Even configured with a CDN, a private key still gets a signed URL."""
        url = self._storage(
            public_base_url="https://photos.example.com",
            access_key_id="k",
            secret_access_key="s",
        ).url("events/r/original/a.jpg", visibility="private")
        assert "photos.example.com" not in url
        assert "X-Amz-Signature=" in url
