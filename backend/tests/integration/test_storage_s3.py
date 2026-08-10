"""S3 backend against MinIO.

This is where the public/private boundary is actually tested. LocalStorage
cannot prove it -- everything under /media is readable -- so the guarantee that
originals are unreachable without a signed URL only holds if these run.

    make up && uv --project backend run pytest -m integration
"""

from __future__ import annotations

import io
import uuid

import httpx
import pytest

from rpf.storage.base import build_key
from rpf.storage.s3 import S3Storage

pytestmark = pytest.mark.integration

ENDPOINT = "http://localhost:9000"
PRIVATE_BUCKET = "race-photos-private"
PUBLIC_BUCKET = "race-photos-public"


@pytest.fixture
def storage() -> S3Storage:
    backend = S3Storage(
        bucket=PRIVATE_BUCKET,
        public_bucket=PUBLIC_BUCKET,
        endpoint_url=ENDPOINT,
        region="us-east-1",
        access_key_id="minioadmin",
        secret_access_key="minioadmin",
        public_base_url=f"{ENDPOINT}/{PUBLIC_BUCKET}",
    )
    try:
        httpx.get(f"{ENDPOINT}/minio/health/live", timeout=2.0)
    except httpx.HTTPError:
        pytest.skip("MinIO is not running (make up)")
    return backend


@pytest.fixture
def keys() -> dict[str, str]:
    photo_id = str(uuid.uuid4())
    return {
        "original": build_key("itest", "original", photo_id),
        "thumb": build_key("itest", "thumb", photo_id),
    }


def test_roundtrip(storage, keys):
    storage.put(keys["thumb"], io.BytesIO(b"thumb-bytes"), visibility="public")
    assert storage.get(keys["thumb"], visibility="public") == b"thumb-bytes"
    storage.delete(keys["thumb"], visibility="public")


def test_missing_key_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.get("events/itest/thumb/does-not-exist.jpg", visibility="public")


def test_public_object_is_readable_without_credentials(storage, keys):
    storage.put(keys["thumb"], io.BytesIO(b"public-bytes"), visibility="public")
    try:
        response = httpx.get(storage.url(keys["thumb"], visibility="public"))
        assert response.status_code == 200
        assert response.content == b"public-bytes"
    finally:
        storage.delete(keys["thumb"], visibility="public")


def test_original_is_not_readable_without_a_signature(storage, keys):
    """The guarantee the paid-download model rests on."""
    storage.put(keys["original"], io.BytesIO(b"secret-bytes"), visibility="private")
    try:
        unsigned = f"{ENDPOINT}/{PRIVATE_BUCKET}/{keys['original']}"
        assert httpx.get(unsigned).status_code == 403

        # ...and it is not hiding in the public bucket either.
        assert httpx.get(f"{ENDPOINT}/{PUBLIC_BUCKET}/{keys['original']}").status_code == 404
    finally:
        storage.delete(keys["original"], visibility="private")


def test_signed_url_grants_access_to_the_original(storage, keys):
    storage.put(keys["original"], io.BytesIO(b"secret-bytes"), visibility="private")
    try:
        response = httpx.get(storage.url(keys["original"], visibility="private"))
        assert response.status_code == 200
        assert response.content == b"secret-bytes"
    finally:
        storage.delete(keys["original"], visibility="private")


def test_originals_and_derivatives_land_in_different_buckets(storage, keys):
    storage.put(keys["original"], io.BytesIO(b"o"), visibility="private")
    storage.put(keys["thumb"], io.BytesIO(b"t"), visibility="public")
    try:
        assert storage.exists(keys["original"], visibility="private") is True
        assert storage.exists(keys["original"], visibility="public") is False
        assert storage.exists(keys["thumb"], visibility="public") is True
        assert storage.exists(keys["thumb"], visibility="private") is False
    finally:
        storage.delete(keys["original"], visibility="private")
        storage.delete(keys["thumb"], visibility="public")
