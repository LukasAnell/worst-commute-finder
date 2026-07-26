from chicago_traffic.models import TrafficSegment


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
