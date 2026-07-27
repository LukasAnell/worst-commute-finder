import csv
import json
from argparse import ArgumentParser, Namespace

from chicago_traffic.client import TrafficClient
from chicago_traffic.models import TrafficAPIError, TrafficSegment

from worst_commute_finder.ranker import get_top_n_worst_segments


def export_to_json(segments: list[TrafficSegment], path: str):
    with open(path, "w") as jsonfile:
        json.dump(
            [segment.__dict__ for segment in segments], jsonfile, indent=4, default=str
        )


def export_to_csv(segments: list[TrafficSegment], path: str):
    with open(path, "w", newline="") as csvfile:
        fieldnames = [
            "segment_id",
            "street",
            "direction",
            "from_street",
            "to_street",
            "length",
            "street_heading",
            "comments",
            "start_lon",
            "start_lat",
            "end_lon",
            "end_lat",
            "current_speed",
            "last_updated",
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for segment in segments:
            writer.writerow(segment.__dict__)


def print_compact(traffic_segments: list[TrafficSegment]):
    for segment in traffic_segments:
        print(
            f"{segment.street} {segment.direction} ({segment.from_street} -> {segment.to_street}): {segment.current_speed} mph"
        )


def print_verbose(traffic_segments: list[TrafficSegment]):
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

    # add argument for verbose output
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display detailed information about each segment",
    )

    # argument for type of output format used in export
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["json", "csv"],
        help="Output format for export",
    )

    ## argument for export file path
    parser.add_argument(
        "-e",
        "--export",
        type=str,
        help="File path to export the results",
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

    # export the results if requested
    if args.export:
        if args.format == "json":
            export_to_json(n_worst_segments, args.export)
        elif args.format == "csv":
            export_to_csv(n_worst_segments, args.export)
        else:
            print("Invalid export format specified. Use 'json' or 'csv'.")
            return

    # print the results
    if args.verbose:
        print_verbose(n_worst_segments)
    else:
        print_compact(n_worst_segments)


if __name__ == "__main__":
    main()
