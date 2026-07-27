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
    historical_speed_dict: dict[int, list[float]] = {}

    for segment in valid_historical_segments:
        # check that the historical segment is from the same day of the week and roughly the same hour as the live segment
        if (
            segment.last_updated.weekday == segment.last_updated.weekday
            and abs(segment.last_updated.hour - segment.last_updated.hour) <= 1
        ):
            if segment.segment_id not in historical_speed_dict:
                historical_speed_dict[segment.segment_id] = []

            historical_speed_dict[segment.segment_id].append(segment.current_speed)

    return list()


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
