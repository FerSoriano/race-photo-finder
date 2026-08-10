"""The parser and normaliser are the only place a wrong bib silently hides a
runner's photos, so they get the most direct coverage."""

from __future__ import annotations

import pytest

from rpf.detection.normalize import normalize_bib, normalize_bibs
from rpf.detection.ollama_detector import parse_response


class TestParseResponse:
    def test_clean_json(self):
        assert parse_response('{"numbers": ["19131", "6133"]}') == ["19131", "6133"]

    def test_json_wrapped_in_prose(self):
        text = 'Here are the numbers:\n{"numbers": ["1234"]}\nHope that helps.'
        assert parse_response(text) == ["1234"]

    def test_empty_list(self):
        assert parse_response('{"numbers": []}') == []

    def test_malformed_json_falls_back_to_digits(self):
        assert parse_response("I can see runner 4076 and 1578") == ["4076", "1578"]

    def test_uncertain_marker_survives_parsing(self):
        assert parse_response('{"numbers": ["?234"]}') == ["?234"]


class TestNormalizeBib:
    @pytest.mark.parametrize(
        ("raw", "number", "uncertain"),
        [
            ("19131", "19131", False),
            ("  6133  ", "6133", False),
            ("?234", "234", True),
            ("0042", "0042", False),  # leading zeros are printed on the bib
            ("A-1234", "1234", False),
        ],
    )
    def test_valid(self, raw, number, uncertain):
        bib = normalize_bib(raw)
        assert bib is not None
        assert (bib.number, bib.is_uncertain) == (number, uncertain)

    @pytest.mark.parametrize("raw", ["", "   ", "abc", "1234567"])
    def test_rejected(self, raw):
        assert normalize_bib(raw) is None


class TestNormalizeBibs:
    def test_matches_the_prototype_output(self):
        """The three bibs the original prototype found in 21k-gdl-3.jpg."""
        bibs = normalize_bibs(["19131", "6133", "13441"])
        assert [b.number for b in bibs] == ["19131", "6133", "13441"]

    def test_deduplicates_preserving_order(self):
        assert [b.number for b in normalize_bibs(["100", "200", "100"])] == ["100", "200"]

    def test_certain_reading_beats_uncertain(self):
        bibs = normalize_bibs(["?1234", "1234"])
        assert len(bibs) == 1
        assert bibs[0].is_uncertain is False

    def test_drops_invalid_entries(self):
        assert [b.number for b in normalize_bibs(["123", "", "xyz"])] == ["123"]
