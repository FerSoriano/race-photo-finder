"""Turns raw model output into storable bib numbers."""

from __future__ import annotations

import re

from rpf.detection.base import Bib

# Bibs shorter than this are almost always a misread fragment (a shoe logo, a
# sponsor sign). Longer ones are usually two bibs read as one.
MIN_BIB_LENGTH = 1
MAX_BIB_LENGTH = 6

_DIGITS = re.compile(r"\d+")


def normalize_bib(raw: str) -> Bib | None:
    """Normalise one raw string from the model.

    The prompt asks the model to mark unsure digits with a leading "?", so
    "?234" becomes an uncertain bib "234". Anything without digits, or outside
    the plausible length range, is dropped.
    """
    raw = raw.strip()
    if not raw:
        return None

    is_uncertain = raw.startswith("?")
    digits = "".join(_DIGITS.findall(raw))
    if not digits:
        return None
    if not MIN_BIB_LENGTH <= len(digits) <= MAX_BIB_LENGTH:
        return None

    # Keep leading zeros: bib "0042" and "42" can both exist at a race, and the
    # runner will type what is printed on their chest.
    return Bib(number=digits, is_uncertain=is_uncertain)


def normalize_bibs(raw_numbers: list[str]) -> list[Bib]:
    """Normalise a batch, dropping duplicates while keeping first-seen order.

    When the same number appears both certain and uncertain, the certain
    reading wins.
    """
    by_number: dict[str, Bib] = {}
    for raw in raw_numbers:
        bib = normalize_bib(raw)
        if bib is None:
            continue
        existing = by_number.get(bib.number)
        if existing is None or (existing.is_uncertain and not bib.is_uncertain):
            by_number[bib.number] = bib
    return list(by_number.values())
