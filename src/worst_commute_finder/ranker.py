from collections import defaultdict

from chicago_traffic.models import TrafficSegment


def group_into_corridors(
    traffic_segments: list[TrafficSegment],
) -> list[list[TrafficSegment]]:
    # group segments by (street, direction)
    grouped_segments: dict[tuple[str, str], list[TrafficSegment]] = defaultdict(list)
    for segment in traffic_segments:
        grouped_segments[(segment.street, segment.direction)].append(segment)

    buckets: list[list[TrafficSegment]] = list(grouped_segments.values())

    corridors: list[list[TrafficSegment]] = []
    for bucket in buckets:
        # sort by start_lat or start_lon depending on street_heading
        if bucket[0].street_heading in ["N", "S"]:
            bucket.sort(key=lambda segment: segment.start_lat)
        else:
            bucket.sort(key=lambda segment: segment.start_lon)

        sub_groups: list[list[TrafficSegment]] = []
        current_group: list[TrafficSegment] = [bucket[0]]

        for segment in bucket[1:]:
            # distance from previos segment's endpoint to next segment's start point
            gap: float = distance_between_segments(current_group[-1], segment)
            if gap > MAX_CORRIDOR_GAP_MILES:
                sub_groups.append(current_group)
                current_group = [segment]
            else:
                current_group.append(segment)
        sub_groups.append(current_group)

        corridors.extend(sub_groups)

    return corridors


def get_top_n_worst_corridors(
    corridors: list[list[TrafficSegment]], n: int
) -> list[tuple[TrafficSegment, int]]:
    if n <= 0:
        raise ValueError("n must be a positive integer")

    worst_per_corridor: list[tuple[TrafficSegment, int]] = []

    for group in corridors:
        # filter out segments without data
        group[:] = [segment for segment in group if segment.has_data]

        # skip groups with no data
        if not group:
            continue

        # find the worst segment in the group, and the group's size
        worst_segment: TrafficSegment = min(
            group, key=lambda segment: segment.current_speed
        )
        segment_count: int = len(group)

        worst_per_corridor.append((worst_segment, segment_count))

    # sort by the worst segment's speed
    worst_per_corridor.sort(key=lambda x: x[0].current_speed)

    # return top n corridors
    if len(worst_per_corridor) >= n:
        return worst_per_corridor[:n]

    return worst_per_corridor


def get_top_n_worst_relative(
    live_segments: list[TrafficSegment],
    historical_segments: list[TrafficSegment],
    n: int,
) -> list[tuple[TrafficSegment, float]]:
    if n <= 0:
        raise ValueError("n must be a positive integer")

    # filter valid segments
    valid_live_segments: list[TrafficSegment] = [
        segment for segment in live_segments if segment.has_data
    ]

    valid_historical_segments: list[TrafficSegment] = [
        segment for segment in historical_segments if segment.has_data
    ]

    # create a dict of historical segments mapping segment_id to a list of speed readings
    historical_speed_dict: dict[tuple[int, int, int], list[float]] = defaultdict(list)

    for segment in valid_historical_segments:
        key: tuple[int, int, int] = (
            segment.segment_id,
            segment.last_updated.weekday(),
            segment.last_updated.hour,
        )
        historical_speed_dict[key].append(segment.current_speed)

    # if there are more than 3 speed readings for a segment, store the average in another dict
    average_historical_speed_dict: dict[tuple[int, int, int], float] = {
        key: sum(speeds) / len(speeds)
        for key, speeds in historical_speed_dict.items()
        if len(speeds) >= 3
    }

    # compute speed difference for each live segment that has a corresponding historical average
    speed_diff_list: list[tuple[TrafficSegment, float]] = []
    for segment in valid_live_segments:
        key = (
            segment.segment_id,
            segment.last_updated.weekday(),
            segment.last_updated.hour,
        )

        if key in average_historical_speed_dict:
            speed_diff: float = (
                segment.current_speed - average_historical_speed_dict[key]
            )
            speed_diff_list.append((segment, speed_diff))

    # sort the list by speed difference
    speed_diff_list.sort(key=lambda x: x[1])

    # only return the top n segments
    if len(speed_diff_list) >= n:
        return speed_diff_list[:n]

    return speed_diff_list


def get_top_n_worst_segments(
    traffic_segments: list[TrafficSegment], n: int
) -> list[TrafficSegment]:
    if n <= 0:
        raise ValueError("n must be a positive integer")

    # filter traffic segments so only ones with data are present
    valid_traffic_segments: list[TrafficSegment] = [
        segment for segment in traffic_segments if segment.has_data
    ]

    # sort segments by their current speed
    valid_traffic_segments.sort(key=lambda segment: segment.current_speed)

    # only return the top n segments
    if len(valid_traffic_segments) >= n:
        return valid_traffic_segments[:n]

    return valid_traffic_segments
