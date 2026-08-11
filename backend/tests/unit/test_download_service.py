from __future__ import annotations

import uuid

import pytest

from rpf.config import Settings
from rpf.services.download import TooManyPhotosError, plan_download


@pytest.fixture
def settings() -> Settings:
    return Settings(max_bulk_download=3)


def test_the_selection_is_returned_in_the_order_it_was_sent(settings):
    """The response pairs up with the rows the runner ticked."""
    ids = [uuid.uuid4() for _ in range(3)]
    assert plan_download(ids, settings) == ids


def test_duplicates_collapse(settings):
    """A UI that sends the same photo twice should not be punished for it."""
    first, second = uuid.uuid4(), uuid.uuid4()
    assert plan_download([first, second, first], settings) == [first, second]


def test_duplicates_are_removed_before_the_cap_is_checked(settings):
    """Four ids naming three photos is a request for three photos."""
    ids = [uuid.uuid4() for _ in range(3)]
    assert plan_download([*ids, ids[0]], settings) == ids


def test_over_the_cap_is_rejected(settings):
    with pytest.raises(TooManyPhotosError) as excinfo:
        plan_download([uuid.uuid4() for _ in range(4)], settings)
    assert excinfo.value.limit == 3
    assert excinfo.value.requested == 4
    # The message reaches the frontend as the 422 detail, so it has to name
    # the actual limit rather than just complaining.
    assert "3" in str(excinfo.value)


def test_the_cap_defaults_to_ten():
    """Read off the field, not an instance: a local .env would skew that."""
    assert Settings.model_fields["max_bulk_download"].default == 10
