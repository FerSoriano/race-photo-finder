"""Generates the three renditions stored for every photo.

  original -- untouched, private, only ever handed out via a signed URL
  preview  -- watermarked, long edge capped, what the runner browses
  thumb    -- small, watermark-free, what the grid loads

Originals staying private from day one is what makes the future paid-download
model a pricing change rather than a re-architecture.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

_EXIF_DATETIME_ORIGINAL = 36867


@dataclass(frozen=True, slots=True)
class Derivatives:
    preview: bytes
    thumb: bytes
    width: int
    height: int
    taken_at: datetime | None


def _open_upright(source: Path | bytes) -> Image.Image:
    image = Image.open(Path(source) if isinstance(source, Path) else io.BytesIO(source))
    # Phones store rotation in EXIF; bake it in so every consumer agrees.
    return ImageOps.exif_transpose(image)


def _taken_at(image: Image.Image) -> datetime | None:
    exif = image.getexif()
    raw = exif.get(_EXIF_DATETIME_ORIGINAL) if exif else None
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _to_jpeg(image: Image.Image, quality: int) -> bytes:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def _watermark(image: Image.Image, text: str) -> Image.Image:
    """Diagonal repeated text, translucent, hard to crop out of a preview."""
    image = image.convert("RGBA")
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    font_size = max(16, image.width // 28)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()

    step_x = max(image.width // 3, 1)
    step_y = max(image.height // 4, 1)
    for y in range(0, image.height, step_y):
        for x in range(0, image.width, step_x):
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 70))

    return Image.alpha_composite(image, layer)


def build(
    source: Path | bytes,
    *,
    preview_max_px: int,
    thumb_max_px: int,
    watermark_text: str,
) -> Derivatives:
    with _open_upright(source) as image:
        width, height = image.size
        taken_at = _taken_at(image)

        preview_img = image.copy()
        preview_img.thumbnail((preview_max_px, preview_max_px), Image.LANCZOS)
        preview = _to_jpeg(_watermark(preview_img, watermark_text), quality=82)

        thumb_img = image.copy()
        thumb_img.thumbnail((thumb_max_px, thumb_max_px), Image.LANCZOS)
        thumb = _to_jpeg(thumb_img, quality=78)

    return Derivatives(preview=preview, thumb=thumb, width=width, height=height, taken_at=taken_at)
