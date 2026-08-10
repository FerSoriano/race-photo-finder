"""Production guardrails.

Each of these corresponds to a misconfiguration that would be silent and
expensive: photos vanishing on redeploy, an open ingest endpoint, or originals
served publicly.
"""

from __future__ import annotations

import pytest

from rpf.config import Settings

PROD = {
    "environment": "prod",
    "admin_api_key": "a-real-secret",
    "storage_backend": "s3",
    "s3_bucket": "photos-private",
    "s3_public_bucket": "photos-public",
}


def test_a_correct_production_config_is_accepted():
    assert Settings(**PROD).environment == "prod"


def test_local_storage_is_rejected_in_production():
    """Container filesystems are ephemeral -- this would lose every photo."""
    with pytest.raises(ValueError, match="ephemeral"):
        Settings(**{**PROD, "storage_backend": "local"})


def test_default_admin_key_is_rejected_in_production():
    with pytest.raises(ValueError, match="development default"):
        Settings(**{**PROD, "admin_api_key": "dev-insecure-key"})


def test_sharing_one_bucket_is_rejected_in_production():
    """Originals must not sit in the publicly readable bucket."""
    with pytest.raises(ValueError, match="must differ"):
        Settings(**{**PROD, "s3_public_bucket": "photos-private"})


def test_development_stays_permissive():
    """None of the above should get in the way locally."""
    settings = Settings(environment="dev", storage_backend="local")
    assert settings.storage_backend == "local"
