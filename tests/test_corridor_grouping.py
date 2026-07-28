from chicago_traffic.models import TrafficSegment

from tests.test_ranker import make_segment
from worst_commute_finder.ranker import (
    MAX_CORRIDOR_GAP_MILES,
    distance_between_segments,
    group_into_corridors,
)

# Assuming MAX_CORRIDOR_GAP_MILES is 2, the following deltas are chosen to be clearly below and above that threshold when converted to miles.
CLOSE_LAT_DELTA: float = 0.01  # ~0.69 miles
FAR_LAT_DELTA: float = 0.05  # ~3.45 miles


def test_single_segment_bucket_is_its_own_corridor():
    segment: TrafficSegment = make_segment(
        segment_id=1,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.81,
        end_lon=-87.70,
    )

    corridors: list[list[TrafficSegment]] = group_into_corridors([segment])

    assert len(corridors) == 1
    assert corridors[0] == [segment]


def test_close_segments_on_same_street_merge_into_one_corridor():
    segment1: TrafficSegment = make_segment(
        segment_id=1,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.81,
        end_lon=-87.70,
    )

    segment2: TrafficSegment = make_segment(
        segment_id=2,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.81 + CLOSE_LAT_DELTA,
        start_lon=-87.70,
        end_lat=41.82 + CLOSE_LAT_DELTA,
        end_lon=-87.70,
    )

    corridors: list[list[TrafficSegment]] = group_into_corridors([segment1, segment2])

    assert len(corridors) == 1
    assert set(s.segment_id for s in corridors[0]) == {1, 2}


def test_far_segments_on_same_street_split_into_separate_corridors():
    segment1: TrafficSegment = make_segment(
        segment_id=1,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.81,
        end_lon=-87.70,
    )

    segment2: TrafficSegment = make_segment(
        segment_id=2,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.81 + FAR_LAT_DELTA,
        start_lon=-87.70,
        end_lat=41.82 + FAR_LAT_DELTA,
        end_lon=-87.70,
    )

    corridors: list[list[TrafficSegment]] = group_into_corridors([segment1, segment2])

    assert len(corridors) == 2
    corridor_ids = sorted(tuple(sorted(s.segment_id for s in c)) for c in corridors)
    assert corridor_ids == [(1,), (2,)]


def test_different_streets_never_merge_regardless_of_distance():
    segment1: TrafficSegment = make_segment(
        segment_id=1,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.81,
        end_lon=-87.70,
    )

    segment2: TrafficSegment = make_segment(
        segment_id=2,
        street="Other St",
        direction="NB",
        street_heading="N",
        start_lat=41.81,
        start_lon=-87.70,
        end_lat=41.82,
        end_lon=-87.70,
    )

    corridors: list[list[TrafficSegment]] = group_into_corridors([segment1, segment2])

    assert len(corridors) == 2


def test_different_directions_never_merge_even_on_same_street():
    segment1: TrafficSegment = make_segment(
        segment_id=1,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.81,
        end_lon=-87.70,
    )

    segment2: TrafficSegment = make_segment(
        segment_id=2,
        street="Test St",
        direction="SB",
        street_heading="S",
        start_lat=41.81,
        start_lon=-87.70,
        end_lat=41.82,
        end_lon=-87.70,
    )

    corridors: list[list[TrafficSegment]] = group_into_corridors([segment1, segment2])

    assert len(corridors) == 2


def test_chain_of_close_segments_all_merge_into_single_corridor():
    # should all merge into one corridor because the gap check is only for consecutive pairs.
    segments: list[TrafficSegment] = [
        make_segment(
            segment_id=i,
            street="Test St",
            direction="NB",
            street_heading="N",
            start_lat=41.80 + i * CLOSE_LAT_DELTA,
            start_lon=-87.70,
            end_lat=41.80 + i * CLOSE_LAT_DELTA + 0.005,
            end_lon=-87.70,
        )
        for i in range(5)
    ]

    corridors: list[list[TrafficSegment]] = group_into_corridors(segments)

    assert len(corridors) == 1
    assert len(corridors[0]) == 5


def test_gap_exactly_at_threshold_boundary():
    # distance_between_segments is used directly here to construct a case
    # that lands as close as practical to MAX_CORRIDOR_GAP_MILES, to document
    # the boundary behavior (currently: strictly greater than splits, equal
    # or less merges). If this is fiddly to hit exactly due to floating point,
    # this test's intent is documentation as much as strict verification --
    # adjust tolerance as needed.
    segment1: TrafficSegment = make_segment(
        segment_id=1,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.80,
        end_lon=-87.70,
    )

    # ~1 degree latitude =~ 69 miles
    delta: float = MAX_CORRIDOR_GAP_MILES / 69.0

    segment2: TrafficSegment = make_segment(
        segment_id=2,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80 + delta,
        start_lon=-87.70,
        end_lat=41.80 + delta,
        end_lon=-87.70,
    )

    gap: float = distance_between_segments(segment1, segment2)

    corridors: list[list[TrafficSegment]] = group_into_corridors([segment1, segment2])

    if gap > MAX_CORRIDOR_GAP_MILES:
        assert len(corridors) == 2
    else:
        assert len(corridors) == 1


def test_sort_order_uses_start_lat_for_north_south_streets():
    # Segments given out of order should still be sorted correctly before gap-checking because the street_heading is N/S
    segment_north = make_segment(
        segment_id=1,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.90,
        start_lon=-87.70,
        end_lat=41.91,
        end_lon=-87.70,
    )

    segment_south = make_segment(
        segment_id=2,
        street="Test St",
        direction="NB",
        street_heading="N",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.81,
        end_lon=-87.70,
    )

    # reverse geographic order
    corridors: list[list[TrafficSegment]] = group_into_corridors(
        [segment_north, segment_south]
    )

    # check that they merge
    assert len(corridors) == 1


def test_sort_order_uses_start_lon_for_east_west_streets():
    segment_east = make_segment(
        segment_id=1,
        street="Test Ave",
        direction="EB",
        street_heading="E",
        start_lat=41.80,
        start_lon=-87.60,
        end_lat=41.80,
        end_lon=-87.61,
    )

    segment_west = make_segment(
        segment_id=2,
        street="Test Ave",
        direction="EB",
        street_heading="E",
        start_lat=41.80,
        start_lon=-87.70,
        end_lat=41.80,
        end_lon=-87.71,
    )

    # passed out of geographic order
    corridors: list[list[TrafficSegment]] = group_into_corridors(
        [segment_east, segment_west]
    )

    # shold be split
    assert len(corridors) == 2


def test_empty_input_returns_empty_list():
    corridors: list[list[TrafficSegment]] = group_into_corridors([])

    assert corridors == []
