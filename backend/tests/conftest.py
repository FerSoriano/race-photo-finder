from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES = REPO_ROOT / "samples" / "photos"


@pytest.fixture
def jpeg_bytes() -> bytes:
    """A small in-memory JPEG, so tests never depend on the sample photos."""
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 800), (30, 90, 160)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_photo() -> Path:
    path = SAMPLES / "21k-gdl-3.jpg"
    if not path.is_file():
        pytest.skip("sample photo not available")
    return path
