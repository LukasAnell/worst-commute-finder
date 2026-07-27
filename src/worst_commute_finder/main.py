from argparse import ArgumentParser, Namespace

from chicago_traffic.client import TrafficClient
from chicago_traffic.models import TrafficAPIError, TrafficSegment

from worst_commute_finder.ranker import get_top_n_worst_segments


def print_formatted_data(traffic_segments: list[TrafficSegment]):
    for segment in traffic_segments:
        print(
            f"Segment ID: {segment.segment_id}, "
            f"Street: {segment.street}, "
            f"Direction: {segment.direction}, "
            f"From: {segment.from_street}, "
            f"To: {segment.to_street}, "
            f"Length: {segment.length} miles, "
            f"Street Heading: {segment.street_heading}, "
            f"Comments: {segment.comments}, "
            f"start_lon: {segment.start_lon}, "
            f"start_lat: {segment.start_lat}, "
            f"end_lon: {segment.end_lon}, "
            f"end_lat: {segment.end_lat}, "
            f"Current Speed: {segment.current_speed} mph, "
            f"Last Updated: {segment.last_updated}"
        )


def main():
    # set up argument parser
    parser: ArgumentParser = ArgumentParser(
        description="Fetch and display the top 10 worst traffic segments in Chicago."
    )

    # add argument for number of worst segments to display
    parser.add_argument(
        "-n",
        "--num-segments",
        type=int,
        default=10,
        help="Number of worst segments to display",
    )

    # parse arguments
    args: Namespace = parser.parse_args()

    # create a TrafficClient instance
    client: TrafficClient = TrafficClient()

    try:
        # fetch live traffic data from the API
        traffic_segments: list[TrafficSegment] = client.get_live_speeds()

        # get the top 10 worst segments based on current speed
        n_worst_segments: list[TrafficSegment] = get_top_n_worst_segments(
            traffic_segments, args.num_segments
        )
    except TrafficAPIError as e:
        print(f"Error fetching traffic data: {e}")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return

    print_formatted_data(n_worst_segments)


if __name__ == "__main__":
    main()
