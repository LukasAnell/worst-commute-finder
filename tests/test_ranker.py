from datetime import datetime, timezone

import pytest
from chicago_traffic.models import TrafficSegment

from worst_commute_finder.ranker import (
    get_top_n_worst_corridors,
    get_top_n_worst_relative,
    get_top_n_worst_segments,
    group_into_corridors,
)


def make_segment(
    segment_id=1,
    street="Test St",
    direction="NB",
    from_street="A",
    to_street="B",
    current_speed=10.0,
    has_data=True,
    last_updated=None,
    **overrides,
) -> TrafficSegment:
    """Helper to build a TrafficSegment object"""
    pass


def test_get_top_n_worst_segments_empty_list():
    """Empty input returns empty output, no error."""
    pass


def test_get_top_n_worst_segments_excludes_no_data():
    """Segments with has_data=False are filtered out entirely."""
    pass


def test_get_top_n_worst_segments_sorts_ascending_by_speed():
    """Slowest segments come first."""
    pass


def test_get_top_n_worst_segments_n_larger_than_available():
    """If n exceeds available segments, return all of them, not an error."""
    pass


def test_get_top_n_worst_segments_n_zero_or_negative_raises():
    """n <= 0 raises ValueError."""
    pass


def test_group_into_corridors_groups_by_street_and_direction():
    """Segments sharing (street, direction) end up in the same group."""
    pass


def test_group_into_corridors_different_direction_separate_groups():
    """Same street, different direction -> separate groups."""
    pass


def test_group_into_corridors_empty_list():
    """Empty input returns empty output."""
    pass


def test_get_top_n_worst_corridors_returns_worst_segment_and_count():
    """Each result tuple is (worst_segment, segment_count) for that corridor."""
    pass


def test_get_top_n_worst_corridors_sorts_by_worst_segment_speed():
    """Corridors sorted ascending by their worst segment's current_speed."""
    pass


def test_get_top_n_worst_corridors_n_larger_than_available():
    """If n exceeds available corridors, return all of them."""
    pass


def test_get_top_n_worst_corridors_n_zero_or_negative_raises():
    """n <= 0 raises ValueError."""
    pass


def test_get_top_n_worst_relative_excludes_fewer_than_three_readings():
    """A segment/weekday/hour key with fewer than 3 historical readings has no
    average computed, so live segments matching that key are excluded from results."""
    pass


def test_get_top_n_worst_relative_computes_speed_difference():
    """speed_diff = live current_speed - historical average for matching (segment_id, weekday, hour)."""
    pass


def test_get_top_n_worst_relative_excludes_no_data_live_and_historical():
    """has_data=False segments excluded from both live and historical inputs."""
    pass


def test_get_top_n_worst_relative_no_matching_historical_key_excluded():
    """Live segment with no corresponding historical average (no key match) is excluded, not errored."""
    pass


def test_get_top_n_worst_relative_n_zero_or_negative_raises():
    """n <= 0 raises ValueError."""
    pass
