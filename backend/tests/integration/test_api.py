"""End-to-end API tests against a real Postgres.

make up && make migrate && uv --project backend run pytest -m integration
"""

from __future__ import annotations

import hashlib
import io
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image
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
        # Pinned rather than inherited: a developer's .env must not decide
        # whether the bulk-download cap test passes.
        max_bulk_download=10,
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

    def test_publish_makes_it_visible(self, client, admin):
        client.post(
            "/v1/admin/events",
            headers=admin,
            json={"slug": "itest-publish", "name": "Draft"},
        )
        try:
            assert client.get("/v1/events/itest-publish").status_code == 404

            response = client.patch(
                "/v1/admin/events/itest-publish", headers=admin, json={"is_published": True}
            )
            assert response.status_code == 200
            assert response.json()["is_published"] is True
            assert client.get("/v1/events/itest-publish").status_code == 200
        finally:
            with get_session_factory()() as db:
                db.execute(text("DELETE FROM events WHERE slug = 'itest-publish'"))
                db.commit()

    def test_unpublish_hides_it_again_without_deleting_it(self, client, admin, event, jpeg_bytes):
        _upload(client, admin, jpeg_bytes, ["19131"])

        response = client.patch(
            f"/v1/admin/events/{SLUG}", headers=admin, json={"is_published": False}
        )
        assert response.status_code == 200
        assert response.json()["is_published"] is False
        assert client.get(f"/v1/events/{SLUG}").status_code == 404

        # The row itself is untouched -- only public visibility changed. The
        # public search 404s along with the event (it also requires
        # PublishedEvent), so check via the admin-only hashes endpoint instead.
        hashes = client.get(f"/v1/admin/events/{SLUG}/photos/hashes", headers=admin).json()
        assert len(hashes) == 1
        assert client.get(f"/v1/events/{SLUG}/photos", params={"bib": "19131"}).status_code == 404

    def test_update_only_touches_fields_that_were_sent(self, client, admin, event):
        response = client.patch(
            f"/v1/admin/events/{SLUG}", headers=admin, json={"location": "Guadalajara"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["location"] == "Guadalajara"
        assert body["name"] == "Integration Race"
        assert body["is_published"] is True

    def test_update_requires_admin_key(self, client, event):
        response = client.patch(f"/v1/admin/events/{SLUG}", json={"is_published": True})
        assert response.status_code == 401

    def test_update_unknown_event_is_a_404(self, client, admin):
        response = client.patch(
            "/v1/admin/events/itest-nope", headers=admin, json={"is_published": True}
        )
        assert response.status_code == 404


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


class TestCover:
    """The admin-only cover image endpoints -- see services/cover.py."""

    def test_upload_sets_cover_url(self, client, admin, event, jpeg_bytes):
        response = client.post(
            f"/v1/admin/events/{SLUG}/cover",
            headers=admin,
            files={"file": ("cover.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["cover_url"] is not None
        assert f"events/{SLUG}/cover.jpg" in body["cover_url"]

        # The public read paths (list + detail) pick it up too.
        detail = client.get(f"/v1/events/{SLUG}").json()
        assert detail["cover_url"] == body["cover_url"]

    def test_upload_requires_admin_key(self, client, event, jpeg_bytes):
        response = client.post(
            f"/v1/admin/events/{SLUG}/cover",
            files={"file": ("cover.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert response.status_code == 401

    def test_upload_rejects_a_non_image_file(self, client, admin, event):
        response = client.post(
            f"/v1/admin/events/{SLUG}/cover",
            headers=admin,
            files={"file": ("cover.txt", b"not an image", "text/plain")},
        )
        assert response.status_code == 422
        assert "not a valid image" in response.json()["detail"]

    def test_upload_rejects_a_file_over_the_size_cap(self, client, admin, event):
        oversized = b"0" * (5 * 1024 * 1024 + 1)
        response = client.post(
            f"/v1/admin/events/{SLUG}/cover",
            headers=admin,
            files={"file": ("cover.jpg", oversized, "image/jpeg")},
        )
        assert response.status_code == 422
        assert "limit is" in response.json()["detail"]

    def test_delete_clears_the_cover_url(self, client, admin, event, jpeg_bytes):
        client.post(
            f"/v1/admin/events/{SLUG}/cover",
            headers=admin,
            files={"file": ("cover.jpg", jpeg_bytes, "image/jpeg")},
        )
        response = client.delete(f"/v1/admin/events/{SLUG}/cover", headers=admin)
        assert response.status_code == 200
        assert response.json()["cover_url"] is None

        detail = client.get(f"/v1/events/{SLUG}").json()
        assert detail["cover_url"] is None

    def test_delete_requires_admin_key(self, client, event):
        response = client.delete(f"/v1/admin/events/{SLUG}/cover")
        assert response.status_code == 401

    def test_reupload_in_a_different_format_replaces_the_old_key(
        self, client, admin, event, jpeg_bytes
    ):
        png_buffer = io.BytesIO()
        Image.new("RGB", (100, 100), (10, 20, 30)).save(png_buffer, format="PNG")

        client.post(
            f"/v1/admin/events/{SLUG}/cover",
            headers=admin,
            files={"file": ("cover.jpg", jpeg_bytes, "image/jpeg")},
        )
        response = client.post(
            f"/v1/admin/events/{SLUG}/cover",
            headers=admin,
            files={"file": ("cover.png", png_buffer.getvalue(), "image/png")},
        )
        assert response.status_code == 200
        assert f"events/{SLUG}/cover.png" in response.json()["cover_url"]


class TestAdminStats:
    """The dashboard's counts. The integration DB is not truncated between
    tests -- assert deltas, never absolute counts."""

    def test_counts_move_by_exactly_what_was_created(self, client, admin, event, jpeg_bytes):
        before = client.get("/v1/admin/stats", headers=admin).json()

        client.post(
            "/v1/admin/events", headers=admin, json={"slug": "itest-draft", "name": "Draft"}
        )
        _upload(client, admin, jpeg_bytes, ["19131"])
        try:
            after = client.get("/v1/admin/stats", headers=admin).json()
            assert after["events_total"] == before["events_total"] + 1
            assert after["events_draft"] == before["events_draft"] + 1
            assert after["events_published"] == before["events_published"]
            assert after["photos_total"] == before["photos_total"] + 1
        finally:
            with get_session_factory()() as db:
                db.execute(text("DELETE FROM events WHERE slug = 'itest-draft'"))
                db.commit()

    def test_requires_admin_key(self, client):
        assert client.get("/v1/admin/stats").status_code == 401


class TestAdminEventList:
    def test_lists_drafts_the_public_route_hides(self, client, admin):
        client.post(
            "/v1/admin/events", headers=admin, json={"slug": "itest-draft-list", "name": "Draft"}
        )
        try:
            admin_slugs = {e["slug"] for e in client.get("/v1/admin/events", headers=admin).json()}
            assert "itest-draft-list" in admin_slugs
            public_slugs = {e["slug"] for e in client.get("/v1/events").json()}
            assert "itest-draft-list" not in public_slugs
        finally:
            with get_session_factory()() as db:
                db.execute(text("DELETE FROM events WHERE slug = 'itest-draft-list'"))
                db.commit()

    def test_rows_carry_the_photo_count(self, client, admin, event, jpeg_bytes):
        _upload(client, admin, jpeg_bytes, ["1"], "a.jpg")
        _upload(client, admin, jpeg_bytes + b"x", ["2"], "b.jpg")
        rows = client.get("/v1/admin/events", headers=admin).json()
        row = next(r for r in rows if r["slug"] == SLUG)
        assert row["photo_count"] == 2

    def test_an_event_with_no_photos_reports_zero(self, client, admin, event):
        """Regression guard: counts_by_event's GROUP BY omits events with zero
        photos, so a missing `.get(id, 0)` would drop the row or crash."""
        rows = client.get("/v1/admin/events", headers=admin).json()
        row = next(r for r in rows if r["slug"] == SLUG)
        assert row["photo_count"] == 0

    def test_requires_admin_key(self, client):
        assert client.get("/v1/admin/events").status_code == 401


class TestAdminEventDetail:
    def test_reaches_a_draft(self, client, admin):
        """Unlike the public GET /v1/events/{slug}, which 404s on a draft."""
        client.post(
            "/v1/admin/events", headers=admin, json={"slug": "itest-draft-detail", "name": "Draft"}
        )
        try:
            response = client.get("/v1/admin/events/itest-draft-detail", headers=admin)
            assert response.status_code == 200
            assert response.json()["is_published"] is False
        finally:
            with get_session_factory()() as db:
                db.execute(text("DELETE FROM events WHERE slug = 'itest-draft-detail'"))
                db.commit()

    def test_carries_the_photo_count(self, client, admin, event, jpeg_bytes):
        _upload(client, admin, jpeg_bytes, ["19131"])
        response = client.get(f"/v1/admin/events/{SLUG}", headers=admin)
        assert response.json()["photo_count"] == 1

    def test_unknown_event_is_a_404(self, client, admin):
        assert client.get("/v1/admin/events/itest-nope", headers=admin).status_code == 404

    def test_requires_admin_key(self, client, event):
        assert client.get(f"/v1/admin/events/{SLUG}").status_code == 401


class TestAdminEventDelete:
    """The one destructive route. Storage cleanup isn't observable through the
    API, so these check tmp_path directly -- the `client` fixture pins
    local_storage_root to it."""

    def test_delete_removes_the_row_and_its_photos(self, client, admin, event, jpeg_bytes):
        _upload(client, admin, jpeg_bytes, ["19131"])
        assert client.delete(f"/v1/admin/events/{SLUG}", headers=admin).status_code == 204

        assert (
            client.get(f"/v1/admin/events/{SLUG}/photos/hashes", headers=admin).status_code == 404
        )
        assert client.get(f"/v1/events/{SLUG}").status_code == 404

        # Recreating the same slug proves the row is gone, not merely hidden --
        # a lingering row would 409 here.
        recreated = client.post(
            "/v1/admin/events", headers=admin, json={"slug": SLUG, "name": "again"}
        )
        assert recreated.status_code == 201

    def test_delete_removes_the_stored_objects(self, client, admin, event, jpeg_bytes, tmp_path):
        _upload(client, admin, jpeg_bytes, ["19131"])
        event_dir = tmp_path / "events" / SLUG
        assert any(p.is_file() for p in event_dir.rglob("*"))

        assert client.delete(f"/v1/admin/events/{SLUG}", headers=admin).status_code == 204
        # `delete_many` unlinks files but leaves empty directories behind --
        # that is fine, only leftover *objects* would be a bug.
        assert not any(p.is_file() for p in event_dir.rglob("*"))

    def test_delete_removes_the_cover_object(self, client, admin, event, jpeg_bytes, tmp_path):
        client.post(
            f"/v1/admin/events/{SLUG}/cover",
            headers=admin,
            files={"file": ("cover.jpg", jpeg_bytes, "image/jpeg")},
        )
        cover_path = tmp_path / "events" / SLUG / "cover.jpg"
        assert cover_path.exists()

        assert client.delete(f"/v1/admin/events/{SLUG}", headers=admin).status_code == 204
        assert not cover_path.exists()

    def test_delete_leaves_another_events_objects_alone(
        self, client, admin, event, jpeg_bytes, tmp_path
    ):
        """Guards against ever "optimising" the sweep into a prefix delete."""
        _upload(client, admin, jpeg_bytes, ["19131"])
        assert (
            client.post(
                "/v1/admin/events",
                headers=admin,
                json={"slug": "itest-other-delete", "name": "Other", "is_published": True},
            ).status_code
            == 201
        )
        try:
            other_bytes = jpeg_bytes + b"other"
            client.post(
                "/v1/admin/events/itest-other-delete/photos",
                headers=admin,
                files={"file": ("q.jpg", other_bytes, "image/jpeg")},
                data={"sha256": hashlib.sha256(other_bytes).hexdigest(), "bibs": "[]"},
            )
            assert client.delete(f"/v1/admin/events/{SLUG}", headers=admin).status_code == 204
            assert any((tmp_path / "events" / "itest-other-delete").rglob("*"))
        finally:
            with get_session_factory()() as db:
                db.execute(text("DELETE FROM events WHERE slug = 'itest-other-delete'"))
                db.commit()

    def test_delete_unknown_event_is_a_404(self, client, admin):
        assert client.delete("/v1/admin/events/itest-nope", headers=admin).status_code == 404

    def test_delete_requires_admin_key(self, client, event):
        assert client.delete(f"/v1/admin/events/{SLUG}").status_code == 401


class TestBulkDownload:
    """One call for the whole gallery selection -- see services/download.py."""

    def _ids(self, client, admin, jpeg_bytes, count):
        # Distinct bytes per photo: ingest is idempotent by sha256, so identical
        # files would collapse into one row.
        ids = []
        for index in range(count):
            content = jpeg_bytes + bytes([index])
            ids.append(_upload(client, admin, content, ["19131"], f"p{index}.jpg").json()["id"])
        return ids

    def test_links_come_back_in_the_order_they_were_asked_for(
        self, client, admin, event, jpeg_bytes
    ):
        ids = self._ids(client, admin, jpeg_bytes, 3)
        selection = [ids[2], ids[0], ids[1]]

        body = client.post(
            f"/v1/events/{SLUG}/photos/download", json={"photo_ids": selection}
        ).json()

        assert [p["id"] for p in body["photos"]] == selection
        assert body["event_slug"] == SLUG
        assert body["expires_in"] > 0

    def test_each_link_carries_the_uploaded_filename(self, client, admin, event, jpeg_bytes):
        """A runner must not end up with ten UUID-named files."""
        ids = self._ids(client, admin, jpeg_bytes, 2)
        body = client.post(f"/v1/events/{SLUG}/photos/download", json={"photo_ids": ids}).json()
        assert [p["filename"] for p in body["photos"]] == ["p0.jpg", "p1.jpg"]

    def test_links_point_at_originals_only(self, client, admin, event, jpeg_bytes):
        ids = self._ids(client, admin, jpeg_bytes, 1)
        body = client.post(f"/v1/events/{SLUG}/photos/download", json={"photo_ids": ids}).text
        assert "/thumb/" not in body
        assert "/preview/" not in body
        assert "storage_key_original" not in body

    def test_duplicates_collapse_to_one_link(self, client, admin, event, jpeg_bytes):
        ids = self._ids(client, admin, jpeg_bytes, 1)
        body = client.post(f"/v1/events/{SLUG}/photos/download", json={"photo_ids": ids * 3}).json()
        assert len(body["photos"]) == 1

    def test_over_the_cap_is_rejected(self, client, admin, event, jpeg_bytes):
        too_many = [str(uuid.uuid4()) for _ in range(11)]
        response = client.post(f"/v1/events/{SLUG}/photos/download", json={"photo_ids": too_many})
        assert response.status_code == 422
        # Rejected on the count alone -- no lookup of ids we will not serve.
        assert "limit is 10" in response.json()["detail"]

    def test_an_empty_selection_is_rejected(self, client, admin, event):
        response = client.post(f"/v1/events/{SLUG}/photos/download", json={"photo_ids": []})
        assert response.status_code == 422

    def test_one_unknown_id_fails_the_whole_request(self, client, admin, event, jpeg_bytes):
        """A stale selection should say so, not quietly come up short."""
        ids = self._ids(client, admin, jpeg_bytes, 1)
        missing = str(uuid.uuid4())
        response = client.post(
            f"/v1/events/{SLUG}/photos/download", json={"photo_ids": [*ids, missing]}
        )
        assert response.status_code == 404
        assert missing in response.json()["detail"]

    def test_a_photo_of_another_event_is_not_reachable(self, client, admin, event, jpeg_bytes):
        """Ids are resolved scoped to the event, so borrowing one fails."""
        ids = self._ids(client, admin, jpeg_bytes, 1)
        client.post(
            "/v1/admin/events",
            headers=admin,
            json={"slug": "itest-other", "name": "Other", "is_published": True},
        )
        try:
            response = client.post(
                "/v1/events/itest-other/photos/download", json={"photo_ids": ids}
            )
            assert response.status_code == 404
        finally:
            with get_session_factory()() as db:
                db.execute(text("DELETE FROM events WHERE slug = 'itest-other'"))
                db.commit()

    def test_an_unknown_event_is_a_404(self, client):
        response = client.post(
            "/v1/events/itest-nope/photos/download", json={"photo_ids": [str(uuid.uuid4())]}
        )
        assert response.status_code == 404
