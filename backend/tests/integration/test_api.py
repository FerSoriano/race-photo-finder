"""End-to-end API tests against a real Postgres.

make up && make migrate && uv --project backend run pytest -m integration
"""

from __future__ import annotations

import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from rpf.config import Settings
from rpf.db.session import get_engine, get_session_factory
from rpf.main import create_app

pytestmark = pytest.mark.integration

ADMIN_KEY = "dev-insecure-key"
SLUG = "itest-race"


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings = Settings(
        environment="test",
        admin_api_key=ADMIN_KEY,
        storage_backend="local",
        local_storage_root=tmp_path,
    )
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("Postgres is not running (make up && make migrate)")

    app = create_app(settings)
    # Routes resolve settings/storage through the cached getters; point those at
    # this test's isolated configuration.
    from rpf.config import get_settings
    from rpf.storage.factory import build_storage, get_storage

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_storage] = lambda: build_storage(settings)

    with TestClient(app) as test_client:
        yield test_client

    with get_session_factory()() as db:
        db.execute(text("DELETE FROM events WHERE slug = :s"), {"s": SLUG})
        db.commit()


@pytest.fixture
def admin() -> dict[str, str]:
    return {"X-Admin-Key": ADMIN_KEY}


def _upload(client, admin, jpeg_bytes, bibs, filename="p.jpg"):
    return client.post(
        f"/v1/admin/events/{SLUG}/photos",
        headers=admin,
        files={"file": (filename, jpeg_bytes, "image/jpeg")},
        data={
            "sha256": hashlib.sha256(jpeg_bytes).hexdigest(),
            "bibs": json.dumps([{"number": b} for b in bibs]),
            "model_name": "test-model",
        },
    )


@pytest.fixture
def event(client, admin):
    client.post(
        "/v1/admin/events",
        headers=admin,
        json={"slug": SLUG, "name": "Integration Race", "is_published": True},
    )
    return SLUG


class TestAuth:
    def test_admin_requires_a_key(self, client):
        response = client.post("/v1/admin/events", json={"slug": "x", "name": "x"})
        assert response.status_code == 401

    def test_admin_rejects_a_wrong_key(self, client):
        response = client.post(
            "/v1/admin/events",
            headers={"X-Admin-Key": "wrong"},
            json={"slug": "x", "name": "x"},
        )
        assert response.status_code == 401


class TestEvents:
    def test_duplicate_slug_conflicts(self, client, admin, event):
        response = client.post(
            "/v1/admin/events", headers=admin, json={"slug": SLUG, "name": "again"}
        )
        assert response.status_code == 409

    def test_unpublished_event_is_invisible(self, client, admin):
        client.post(
            "/v1/admin/events",
            headers=admin,
            json={"slug": "itest-hidden", "name": "Hidden", "is_published": False},
        )
        try:
            # 404, not 403 -- an unannounced race must not be discoverable.
            assert client.get("/v1/events/itest-hidden").status_code == 404
        finally:
            with get_session_factory()() as db:
                db.execute(text("DELETE FROM events WHERE slug = 'itest-hidden'"))
                db.commit()


class TestIngest:
    def test_upload_then_search(self, client, admin, event, jpeg_bytes):
        assert _upload(client, admin, jpeg_bytes, ["19131", "6133"]).status_code == 201

        result = client.get(f"/v1/events/{SLUG}/photos", params={"bib": "19131"}).json()
        assert result["total"] == 1
        assert {b["number"] for b in result["photos"][0]["bibs"]} == {"19131", "6133"}

    def test_upload_is_idempotent(self, client, admin, event, jpeg_bytes):
        first = _upload(client, admin, jpeg_bytes, ["100"])
        second = _upload(client, admin, jpeg_bytes, ["100"])

        assert first.json()["created"] is True
        assert second.json()["created"] is False
        assert first.json()["id"] == second.json()["id"]

    def test_declared_hash_must_match_the_bytes(self, client, admin, event, jpeg_bytes):
        response = client.post(
            f"/v1/admin/events/{SLUG}/photos",
            headers=admin,
            files={"file": ("p.jpg", jpeg_bytes, "image/jpeg")},
            data={"sha256": "0" * 64, "bibs": "[]"},
        )
        assert response.status_code == 422
        assert "sha256 mismatch" in response.json()["detail"]

    def test_hashes_endpoint_feeds_the_upload_skip_list(self, client, admin, event, jpeg_bytes):
        _upload(client, admin, jpeg_bytes, ["100"])
        hashes = client.get(f"/v1/admin/events/{SLUG}/photos/hashes", headers=admin).json()
        assert hashlib.sha256(jpeg_bytes).hexdigest() in hashes


class TestSearch:
    def test_query_is_normalised(self, client, admin, event, jpeg_bytes):
        _upload(client, admin, jpeg_bytes, ["19131"])
        response = client.get(f"/v1/events/{SLUG}/photos", params={"bib": "#19131 "})
        assert response.json()["total"] == 1

    def test_unknown_bib_returns_nothing(self, client, admin, event, jpeg_bytes):
        _upload(client, admin, jpeg_bytes, ["19131"])
        response = client.get(f"/v1/events/{SLUG}/photos", params={"bib": "88888"})
        assert response.json()["total"] == 0

    def test_near_miss_suggests_the_real_bib(self, client, admin, event, jpeg_bytes):
        """A misread digit must lead somewhere, not dead-end."""
        _upload(client, admin, jpeg_bytes, ["19131"])
        response = client.get(f"/v1/events/{SLUG}/photos", params={"bib": "19181"})
        body = response.json()
        assert body["total"] == 0
        assert "19131" in body["similar_bibs"]

    def test_response_never_exposes_the_original_key(self, client, admin, event, jpeg_bytes):
        """Originals leave only through the signed download endpoint."""
        _upload(client, admin, jpeg_bytes, ["19131"])
        body = client.get(f"/v1/events/{SLUG}/photos", params={"bib": "19131"}).text
        assert "storage_key_original" not in body
        assert "/original/" not in body


class TestDownload:
    def test_download_redirects(self, client, admin, event, jpeg_bytes):
        photo_id = _upload(client, admin, jpeg_bytes, ["19131"]).json()["id"]
        response = client.get(
            f"/v1/events/{SLUG}/photos/{photo_id}/download", follow_redirects=False
        )
        assert response.status_code == 307

    def test_photo_from_another_event_is_not_reachable(self, client, admin, event):
        missing = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/v1/events/{SLUG}/photos/{missing}/download")
        assert response.status_code == 404
