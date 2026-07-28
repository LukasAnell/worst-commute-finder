from datetime import UTC, datetime, timedelta

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
    length=0.5,
    street_heading="N",
    comments=None,
    start_lon=-87.65,
    start_lat=41.85,
    end_lon=-87.65,
    end_lat=41.86,
    **overrides,
) -> TrafficSegment:
    """Helper to build a TrafficSegment object"""
    if last_updated is None:
        last_updated = datetime.now(UTC)

    return TrafficSegment(
        segment_id=segment_id,
        street=street,
        direction=direction,
        from_street=from_street,
        to_street=to_street,
        length=length,
        street_heading=street_heading,
        comments=comments,
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
        current_speed=current_speed if has_data else -1,
        last_updated=last_updated,
        **overrides,
    )


def test_get_top_n_worst_segments_empty_list():
    """Empty input returns empty output, no error."""
    worst_segments: list[TrafficSegment] = get_top_n_worst_segments([], n=5)

    assert worst_segments == []


def test_get_top_n_worst_segments_excludes_no_data():
    """Segments with has_data=False are filtered out entirely."""
    segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0, has_data=True),
        make_segment(segment_id=2, current_speed=5.0, has_data=False),
        make_segment(segment_id=3, current_speed=15.0, has_data=True),
    ]

    worst_segments: list[TrafficSegment] = get_top_n_worst_segments(segments, n=5)

    assert len(worst_segments) == 2


def test_get_top_n_worst_segments_sorts_ascending_by_speed():
    """Slowest segments come first."""
    segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0),
        make_segment(segment_id=2, current_speed=5.0),
        make_segment(segment_id=3, current_speed=15.0),
    ]

    worst_segments: list[TrafficSegment] = get_top_n_worst_segments(segments, n=3)

    assert worst_segments[0].segment_id == 2
    assert worst_segments[1].segment_id == 1
    assert worst_segments[2].segment_id == 3


def test_get_top_n_worst_segments_n_larger_than_available():
    """If n exceeds available segments, return all of them, not an error."""
    segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0),
        make_segment(segment_id=2, current_speed=5.0),
    ]

    worst_segments: list[TrafficSegment] = get_top_n_worst_segments(segments, n=5)

    assert len(worst_segments) == 2


def test_get_top_n_worst_segments_n_zero_or_negative_raises():
    """n <= 0 raises ValueError."""
    segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0),
        make_segment(segment_id=2, current_speed=5.0),
    ]

    with pytest.raises(ValueError):
        get_top_n_worst_segments(segments, n=0)


def test_group_into_corridors_groups_by_street_and_direction():
    """Segments sharing (street, direction) end up in the same group."""
    segments: list[TrafficSegment] = [
        make_segment(segment_id=1, street="Main St", direction="NB"),
        make_segment(segment_id=2, street="Main St", direction="NB"),
        make_segment(segment_id=3, street="Main St", direction="SB"),
        make_segment(segment_id=4, street="Broadway", direction="NB"),
    ]

    corridors: list[list[TrafficSegment]] = group_into_corridors(segments)

    assert len(corridors) == 3
    assert any(
        len(group) == 2
        for group in corridors
        if group[0].street == "Main St" and group[0].direction == "NB"
    )
    assert any(
        len(group) == 1
        for group in corridors
        if group[0].street == "Main St" and group[0].direction == "SB"
    )
    assert any(
        len(group) == 1
        for group in corridors
        if group[0].street == "Broadway" and group[0].direction == "NB"
    )


def test_group_into_corridors_different_direction_separate_groups():
    """Same street, different direction -> separate groups."""
    segments: list[TrafficSegment] = [
        make_segment(segment_id=1, street="Main St", direction="NB"),
        make_segment(segment_id=2, street="Main St", direction="SB"),
    ]

    corridors: list[list[TrafficSegment]] = group_into_corridors(segments)

    assert len(corridors) == 2
    assert all(len(group) == 1 for group in corridors)


def test_group_into_corridors_empty_list():
    """Empty input returns empty output."""
    corridors: list[list[TrafficSegment]] = group_into_corridors([])

    assert corridors == []


def test_get_top_n_worst_corridors_returns_worst_segment_and_count():
    """Each result tuple is (worst_segment, segment_count) for that corridor."""
    segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, street="Main St", direction="NB", current_speed=10.0
        ),
        make_segment(segment_id=2, street="Main St", direction="NB", current_speed=5.0),
        make_segment(
            segment_id=3, street="Broadway", direction="NB", current_speed=15.0
        ),
    ]

    corridors: list[list[TrafficSegment]] = group_into_corridors(segments)

    worst_corridors: list[tuple[TrafficSegment, int]] = get_top_n_worst_corridors(
        corridors, n=2
    )

    assert len(worst_corridors) == 2
    assert worst_corridors[0][0].segment_id == 2  # worst segment
    assert worst_corridors[0][1] == 2  # count of segments in that corridor
    assert worst_corridors[1][0].segment_id == 3
    assert worst_corridors[1][1] == 1


def test_get_top_n_worst_corridors_sorts_by_worst_segment_speed():
    """Corridors sorted ascending by their worst segment's current_speed."""
    segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, street="Main St", direction="NB", current_speed=10.0
        ),
        make_segment(segment_id=2, street="Main St", direction="NB", current_speed=5.0),
        make_segment(
            segment_id=3, street="Broadway", direction="NB", current_speed=15.0
        ),
    ]

    corridors: list[list[TrafficSegment]] = group_into_corridors(segments)

    worst_corridors: list[tuple[TrafficSegment, int]] = get_top_n_worst_corridors(
        corridors, n=2
    )

    assert worst_corridors[0][0].segment_id == 2  # slowest segment
    assert worst_corridors[1][0].segment_id == 3  # next slowest


def test_get_top_n_worst_corridors_n_larger_than_available():
    """If n exceeds available corridors, return all of them."""
    segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, street="Main St", direction="NB", current_speed=10.0
        ),
        make_segment(segment_id=2, street="Main St", direction="NB", current_speed=5.0),
    ]

    corridors: list[list[TrafficSegment]] = group_into_corridors(segments)

    worst_corridors: list[tuple[TrafficSegment, int]] = get_top_n_worst_corridors(
        corridors, n=5
    )

    assert len(worst_corridors) == 1  # only one corridor exists


def test_get_top_n_worst_corridors_n_zero_or_negative_raises():
    """n <= 0 raises ValueError."""
    segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, street="Main St", direction="NB", current_speed=10.0
        ),
        make_segment(segment_id=2, street="Main St", direction="NB", current_speed=5.0),
    ]

    corridors: list[list[TrafficSegment]] = group_into_corridors(segments)

    with pytest.raises(ValueError):
        get_top_n_worst_corridors(corridors, n=0)


def test_get_top_n_worst_relative_excludes_fewer_than_three_readings():
    """A segment/weekday/hour key with fewer than 3 historical readings has no
    average computed, so live segments matching that key are excluded from results."""
    live_time = datetime(2026, 1, 5, 8, 0, 0, tzinfo=UTC)  # arbitrary fixed Monday 8am

    live_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0, last_updated=live_time),
        make_segment(segment_id=2, current_speed=5.0, last_updated=live_time),
    ]

    historical_segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, current_speed=15.0, last_updated=live_time - timedelta(days=7)
        ),
        make_segment(
            segment_id=1,
            current_speed=20.0,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=2, current_speed=25.0, last_updated=live_time - timedelta(days=7)
        ),
    ]

    worst_relative: list[tuple[TrafficSegment, float]] = get_top_n_worst_relative(
        live_segments, historical_segments, n=5
    )

    assert (
        len(worst_relative) == 0
    )  # both segments excluded due to insufficient historical data


def test_get_top_n_worst_relative_computes_speed_difference():
    """speed_diff = live current_speed - historical average for matching (segment_id, weekday, hour)."""
    live_time = datetime(2026, 1, 5, 8, 0, 0, tzinfo=UTC)

    live_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0, last_updated=live_time),
        make_segment(segment_id=2, current_speed=5.0, last_updated=live_time),
    ]

    historical_segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, current_speed=15.0, last_updated=live_time - timedelta(days=7)
        ),
        make_segment(
            segment_id=1,
            current_speed=20.0,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=1,
            current_speed=25.0,
            last_updated=live_time - timedelta(days=21),
        ),
        make_segment(
            segment_id=2, current_speed=30.0, last_updated=live_time - timedelta(days=7)
        ),
        make_segment(
            segment_id=2,
            current_speed=35.0,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=2,
            current_speed=40.0,
            last_updated=live_time - timedelta(days=21),
        ),
    ]

    worst_relative: list[tuple[TrafficSegment, float]] = get_top_n_worst_relative(
        live_segments, historical_segments, n=5
    )

    assert len(worst_relative) == 2
    assert (
        worst_relative[0][0].segment_id == 2
    )  # slowest relative to historical average
    assert worst_relative[0][1] == -30.0  # 5 - 35
    assert worst_relative[1][0].segment_id == 1
    assert worst_relative[1][1] == -10.0  # 10 - 20


def test_get_top_n_worst_relative_excludes_no_data_live_and_historical():
    """has_data=False segments excluded from both live and historical inputs."""
    live_time = datetime(2026, 1, 5, 8, 0, 0, tzinfo=UTC)

    live_segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, current_speed=10.0, has_data=True, last_updated=live_time
        ),
        make_segment(
            segment_id=2, current_speed=5.0, has_data=False, last_updated=live_time
        ),
    ]

    historical_segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1,
            current_speed=15.0,
            has_data=True,
            last_updated=live_time - timedelta(days=7),
        ),
        make_segment(
            segment_id=1,
            current_speed=20.0,
            has_data=True,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=1,
            current_speed=25.0,
            has_data=True,
            last_updated=live_time - timedelta(days=21),
        ),
        make_segment(
            segment_id=2,
            current_speed=30.0,
            has_data=False,
            last_updated=live_time - timedelta(days=7),
        ),
        make_segment(
            segment_id=2,
            current_speed=35.0,
            has_data=False,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=2,
            current_speed=40.0,
            has_data=False,
            last_updated=live_time - timedelta(days=21),
        ),
    ]

    worst_relative: list[tuple[TrafficSegment, float]] = get_top_n_worst_relative(
        live_segments, historical_segments, n=5
    )

    assert len(worst_relative) == 1
    assert worst_relative[0][0].segment_id == 1
    assert worst_relative[0][1] == -10.0  # 10 - 20


def test_get_top_n_worst_relative_no_matching_historical_key_excluded():
    """Live segment with no corresponding historical average (no key match) is excluded, not errored."""
    live_time = datetime(2026, 1, 5, 8, 0, 0, tzinfo=UTC)

    live_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0, last_updated=live_time),
        make_segment(segment_id=2, current_speed=5.0, last_updated=live_time),
    ]

    historical_segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1, current_speed=15.0, last_updated=live_time - timedelta(days=7)
        ),
        make_segment(
            segment_id=1,
            current_speed=20.0,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=1,
            current_speed=25.0,
            last_updated=live_time - timedelta(days=21),
        ),
    ]

    worst_relative: list[tuple[TrafficSegment, float]] = get_top_n_worst_relative(
        live_segments, historical_segments, n=5
    )

    assert len(worst_relative) == 1
    assert worst_relative[0][0].segment_id == 1
    assert worst_relative[0][1] == -10.0  # 10 - 20


def test_get_top_n_worst_relative_excludes_historical_reading_at_or_after_live_timestamp():
    """A historical reading at or after the live segment's own last_updated is excluded from its baseline, even if it exactly matches the live reading."""
    live_time: datetime = datetime(2026, 1, 5, 8, 0, 0, tzinfo=UTC)

    live_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=14.0, last_updated=live_time),
    ]

    historical_segments: list[TrafficSegment] = [
        # self-match
        make_segment(segment_id=1, current_speed=14.0, last_updated=live_time),
        # after live timestamp
        make_segment(
            segment_id=1,
            current_speed=10.0,
            last_updated=live_time + timedelta(minutes=5),
        ),
        make_segment(
            segment_id=1, current_speed=48.0, last_updated=live_time - timedelta(days=7)
        ),
        make_segment(
            segment_id=1,
            current_speed=52.0,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=1,
            current_speed=52.0,
            last_updated=live_time - timedelta(days=21),
        ),
    ]

    worst_relative: list[tuple[TrafficSegment, float]] = get_top_n_worst_relative(
        live_segments, historical_segments, n=5
    )

    assert len(worst_relative) == 1

    # average should be (48 + 52 + 52) / 3 = 50.67
    expected_average: float = (48.0 + 52.0 + 52.0) / 3
    assert abs(worst_relative[0][1] - (14.0 - expected_average)) < 0.01


def test_get_top_n_worst_relative_dedupes_repeated_historical_readings():
    """The same reading appearing more than once in historical data is only counted once toward the average."""
    live_time: datetime = datetime(2026, 1, 5, 8, 0, 0, tzinfo=UTC)

    live_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=14.0, last_updated=live_time),
    ]

    reading_a_time: datetime = live_time - timedelta(days=7)
    historical_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=48.0, last_updated=reading_a_time),
        # exact duplicate of the reading above
        make_segment(segment_id=1, current_speed=48.0, last_updated=reading_a_time),
        make_segment(
            segment_id=1,
            current_speed=52.0,
            last_updated=live_time - timedelta(days=14),
        ),
        make_segment(
            segment_id=1,
            current_speed=56.0,
            last_updated=live_time - timedelta(days=21),
        ),
    ]

    worst_relative: list[tuple[TrafficSegment, float]] = get_top_n_worst_relative(
        live_segments, historical_segments, n=5
    )

    assert len(worst_relative) == 1

    # average should treat the duplicate as ONE reading, so (48 + 52 + 56) / 3 = 52.0,
    expected_average: float = (48.0 + 52.0 + 56.0) / 3
    assert abs(worst_relative[0][1] - (14.0 - expected_average)) < 0.01


def test_get_top_n_worst_relative_duplicates_dont_inflate_reading_count_past_threshold():
    """Duplicated readings don't make reading count go over >= 3 threshold."""
    live_time: datetime = datetime(2026, 1, 5, 8, 0, 0, tzinfo=UTC)

    live_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=14.0, last_updated=live_time),
    ]

    # only 2 distinct historical readings, but one is repeated 3x -> 4 raw entries
    reading_a_time: datetime = live_time - timedelta(days=7)
    historical_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=48.0, last_updated=reading_a_time),
        make_segment(segment_id=1, current_speed=48.0, last_updated=reading_a_time),
        make_segment(segment_id=1, current_speed=48.0, last_updated=reading_a_time),
        make_segment(
            segment_id=1,
            current_speed=52.0,
            last_updated=live_time - timedelta(days=14),
        ),
    ]

    worst_relative: list[tuple[TrafficSegment, float]] = get_top_n_worst_relative(
        live_segments, historical_segments, n=5
    )

    # only 2 distinct readings -- below the >= 3 threshold, so no result at all
    assert len(worst_relative) == 0


def test_get_top_n_worst_relative_n_zero_or_negative_raises():
    """n <= 0 raises ValueError."""
    live_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=10.0),
        make_segment(segment_id=2, current_speed=5.0),
    ]

    historical_segments: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=15.0),
        make_segment(segment_id=1, current_speed=20.0),
        make_segment(segment_id=1, current_speed=25.0),
        make_segment(segment_id=2, current_speed=30.0),
        make_segment(segment_id=2, current_speed=35.0),
        make_segment(segment_id=2, current_speed=40.0),
    ]

    with pytest.raises(ValueError):
        get_top_n_worst_relative(live_segments, historical_segments, n=0)
