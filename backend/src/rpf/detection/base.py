"""Bib detection abstraction.

Today the only implementation is the local Ollama vision model. Keeping callers
behind this protocol means a future YOLO + CRNN or PaddleOCR pipeline can be
dropped in without touching the CLI or the ingest service.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Bib:
    number: str
    # The model prefixes a digit it is unsure about with "?" (see PROMPT).
    is_uncertain: bool = False
    confidence: float | None = None


@runtime_checkable
class BibDetector(Protocol):
    @property
    def name(self) -> str:
        """Identifier stored on each detection, e.g. "qwen2.5vl:7b"."""
        ...

    def detect(self, photo: Path) -> list[Bib]:
        """Return every bib number visible in the photo."""
        ...
