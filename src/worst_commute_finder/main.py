from chicago_traffic.client import TrafficClient
from chicago_traffic.models import TrafficAPIError, TrafficSegment

from worst_commute_finder.ranker import get_top_n_worst_segments

client: TrafficClient = TrafficClient()

try:
    # fetch live traffic data from the API
    traffic_segments: list[TrafficSegment] = client.get_live_speeds()

    # get the top 10 worst segments based on current speed
    n_worst_segments: list[TrafficSegment] = get_top_n_worst_segments(
        traffic_segments, 10
    )
except TrafficAPIError as e:
    print(f"Error fetching traffic data: {e}")
    n_worst_segments = []

print(n_worst_segments)
