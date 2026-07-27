from collections import defaultdict

from chicago_traffic.models import TrafficSegment


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
