from __future__ import annotations

import io

from PIL import Image

from rpf.services import derivatives


def _build(jpeg_bytes: bytes):
    return derivatives.build(
        jpeg_bytes, preview_max_px=1600, thumb_max_px=400, watermark_text="rpf"
    )


def test_records_original_dimensions(jpeg_bytes):
    result = _build(jpeg_bytes)
    assert (result.width, result.height) == (1200, 800)


def test_thumb_is_capped(jpeg_bytes):
    thumb = Image.open(io.BytesIO(_build(jpeg_bytes).thumb))
    assert max(thumb.size) <= 400


def test_preview_is_capped_and_not_upscaled(jpeg_bytes):
    preview = Image.open(io.BytesIO(_build(jpeg_bytes).preview))
    assert max(preview.size) <= 1600
    # Source long edge is 1200, so the preview must not grow past it.
    assert max(preview.size) == 1200


def test_thumb_is_smaller_than_preview(jpeg_bytes):
    result = _build(jpeg_bytes)
    assert len(result.thumb) < len(result.preview)


def test_preview_is_watermarked(jpeg_bytes):
    """A flat-colour source gains pixel variance once text is drawn on it."""
    result = _build(jpeg_bytes)
    preview = Image.open(io.BytesIO(result.preview)).convert("L")
    thumb = Image.open(io.BytesIO(result.thumb)).convert("L")

    assert preview.getextrema()[1] - preview.getextrema()[0] > 20
    # The thumb is deliberately clean, so the grid stays readable.
    assert thumb.getextrema()[1] - thumb.getextrema()[0] < 20


def test_outputs_are_jpeg(jpeg_bytes):
    result = _build(jpeg_bytes)
    for data in (result.preview, result.thumb):
        assert Image.open(io.BytesIO(data)).format == "JPEG"
