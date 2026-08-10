"""Bib detection with a local Ollama vision model.

The prompt and JSON parsing are carried over unchanged from the original
`utils/extract_numbers.py` prototype -- they are known to work against the
sample photos.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import ollama

from rpf.detection.base import Bib
from rpf.detection.normalize import normalize_bibs

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

PROMPT = """Analyze this photo from a race/marathon. Identify the runner \
number (bib number) of each runner visible in the image, even \
if it's blurry, at an angle, or partially visible.

Respond ONLY with valid JSON, with no additional text, in this format:
{"numbers": ["1234", "5678"]}

If you don't see any runner number, respond: {"numbers": []}
If a number is partially visible or you're unsure of a digit, include it \
anyway marking it with a "?" at the start (example: "?234")."""


def parse_response(text: str) -> list[str]:
    """Parse the model's JSON reply; fall back to a digit regex if it fails."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            numbers = data.get("numbers", [])
            if isinstance(numbers, list):
                return [str(n).strip() for n in numbers if str(n).strip()]
        except json.JSONDecodeError:
            pass
    return re.findall(r"\d{1,6}", text)


def list_photos(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )


class OllamaBibDetector:
    """Implements `BibDetector` using a local Ollama vision model."""

    def __init__(self, model: str = "qwen2.5vl:7b", host: str | None = None) -> None:
        self._model = model
        self._client = ollama.Client(host=host) if host else ollama

    @property
    def name(self) -> str:
        return self._model

    def detect(self, photo: Path) -> list[Bib]:
        response = self._client.chat(
            model=self._model,
            messages=[{"role": "user", "content": PROMPT, "images": [str(photo)]}],
            options={"temperature": 0},
        )
        return normalize_bibs(parse_response(response["message"]["content"]))
