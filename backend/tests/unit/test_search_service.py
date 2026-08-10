from __future__ import annotations

import pytest

from rpf.services.search import normalize_query


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("19131", "19131"),
        ("  19131  ", "19131"),
        ("#19131", "19131"),
        ("N 19131", "19131"),
        ("0042", "0042"),
        ("abc", ""),
    ],
)
def test_normalize_query(typed, expected):
    """Runners type the bib however it looks on their chest."""
    assert normalize_query(typed) == expected
