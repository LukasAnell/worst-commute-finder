import csv
import json
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta
from typing import Any

from chicago_traffic.client import TrafficClient
from chicago_traffic.models import TrafficAPIError, TrafficSegment

from worst_commute_finder.cache import load_cached_historical, save_historical_cache
from worst_commute_finder.ranker import (
    get_top_n_worst_corridors,
    get_top_n_worst_relative,
    get_top_n_worst_segments,
    group_into_corridors,
)


def relative_export_to_json(segments: list[tuple[TrafficSegment, float]], path: str):
    with open(path, "w") as jsonfile:
        json.dump(
            [
                {
                    **segment.__dict__,
                    "speed_difference_from_historical_average": speed_diff,
                }
                for segment, speed_diff in segments
            ],
            jsonfile,
            indent=4,
            default=lambda o: (
                o.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(o, datetime) else str(o)
            ),
        )


def absolute_export_to_json(segments: list[TrafficSegment], path: str):
    with open(path, "w") as jsonfile:
        json.dump(
            [segment.__dict__ for segment in segments],
            jsonfile,
            indent=4,
            default=lambda o: (
                o.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(o, datetime) else str(o)
            ),
        )


def relative_export_to_csv(segments: list[tuple[TrafficSegment, float]], path: str):
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
            "speed_difference_from_historical_average",
            "last_updated",
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for segment, speed_diff in segments:
            row: dict[str, Any] = segment.__dict__.copy()
            row["speed_difference_from_historical_average"] = speed_diff

            if isinstance(row["last_updated"], datetime):
                row["last_updated"] = row["last_updated"].strftime("%Y-%m-%dT%H:%M:%S")

            writer.writerow(row)


def absolute_export_to_csv(segments: list[TrafficSegment], path: str):
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
            row: dict[str, Any] = segment.__dict__.copy()

            if isinstance(row["last_updated"], datetime):
                row["last_updated"] = row["last_updated"].strftime("%Y-%m-%dT%H:%M:%S")

            writer.writerow(row)


def corridor_print_compact(corridors: list[tuple[TrafficSegment, int]]):
    for segment, count in corridors:
        print(
            f"{segment.street} {segment.direction} ({segment.from_street} -> {segment.to_street}): "
            f"{segment.current_speed} mph (Segments in corridor: {count})"
        )


def relative_print_compact(traffic_segments: list[tuple[TrafficSegment, float]]):
    for segment, speed_diff in traffic_segments:
        print(
            f"{segment.street} {segment.direction} ({segment.from_street} -> {segment.to_street}): "
            f"{segment.current_speed} mph (Speed Difference: {speed_diff:.2f} mph)"
        )


def absolute_print_compact(traffic_segments: list[TrafficSegment]):
    for segment in traffic_segments:
        print(
            f"{segment.street} {segment.direction} ({segment.from_street} -> {segment.to_street}): {segment.current_speed} mph"
        )


def corridor_print_verbose(corridors: list[tuple[TrafficSegment, int]]):
    for segment, count in corridors:
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
            f"Segments in Corridor: {count}, "
            f"Last Updated: {segment.last_updated}"
        )


def relative_print_verbose(traffic_segments: list[tuple[TrafficSegment, float]]):
    for segment, speed_diff in traffic_segments:
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
            f"Speed Difference from Historical Average: {speed_diff:.2f} mph, "
            f"Last Updated: {segment.last_updated}"
        )


def absolute_print_verbose(traffic_segments: list[TrafficSegment]):
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

    # argument for export file path
    parser.add_argument(
        "-e",
        "--export",
        type=str,
        help="File path to export the results",
    )

    # argument for what type of ranking mode to use
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["absolute", "relative", "corridor"],
        default="absolute",
        help="Ranking mode: absolute (current speed), relative (vs. historical baseline), or corridor (grouped by street and direction)",
    )

    # parse arguments
    args: Namespace = parser.parse_args()

    # create a TrafficClient instance
    client: TrafficClient = TrafficClient()

    # initialize variables for worst segments to prevent unbound errors
    n_worst_segments_absolute: list[TrafficSegment] | None = None
    n_worst_segments_relative: list[tuple[TrafficSegment, float]] | None = None
    n_worst_corridors: list[tuple[TrafficSegment, int]] | None = None

    try:
        # fetch live traffic data from the API
        traffic_segments: list[TrafficSegment] = client.get_live_speeds()

        # branch for absolute vs. relative ranking mode
        if args.mode == "absolute":
            # get the top 10 worst segments based on current speed
            n_worst_segments_absolute = get_top_n_worst_segments(
                traffic_segments, args.num_segments
            )
        elif args.mode == "relative":
            # get start date 2 weeks back
            start: datetime = traffic_segments[0].last_updated - timedelta(weeks=2)

            # get segment_ids from live traffic segments w/ data
            segment_ids: list[int] = [
                segment.segment_id for segment in traffic_segments if segment.has_data
            ]

            # get historical traffic data from cache first, then from API if not cached or cache is too old
            historical_segments = load_cached_historical(max_age=timedelta(hours=6))

            if historical_segments is None:
                historical_segments = client.get_historical_speeds(
                    start=start, segment_ids=segment_ids
                )

                save_historical_cache(historical_segments)

            # get worst relative segments
            n_worst_segments_relative = get_top_n_worst_relative(
                traffic_segments, historical_segments, args.num_segments
            )
        elif args.mode == "corridor":
            corridors: list[list[TrafficSegment]] = group_into_corridors(
                traffic_segments
            )

            n_worst_corridors = get_top_n_worst_corridors(corridors, args.num_segments)

    except TrafficAPIError as e:
        print(f"Error fetching traffic data: {e}")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return

    # print the results based on the mode and verbosity
    if args.mode == "absolute" and n_worst_segments_absolute is not None:
        if args.verbose:
            absolute_print_verbose(n_worst_segments_absolute)
        else:
            absolute_print_compact(n_worst_segments_absolute)

        # export if specified
        if args.export:
            if args.format == "json":
                absolute_export_to_json(n_worst_segments_absolute, args.export)
            elif args.format == "csv":
                absolute_export_to_csv(n_worst_segments_absolute, args.export)
            else:
                if args.format is None:
                    print("Export format not specified. Use '-f json' or '-f csv'.")
                else:
                    print(
                        f"Unsupported export format: {args.format}. Use '-f json' or '-f csv'."
                    )
                return
    elif args.mode == "relative" and n_worst_segments_relative is not None:
        if args.verbose:
            relative_print_verbose(n_worst_segments_relative)
        else:
            relative_print_compact(n_worst_segments_relative)

        # export if specified
        if args.export:
            if args.format == "json":
                relative_export_to_json(n_worst_segments_relative, args.export)
            elif args.format == "csv":
                relative_export_to_csv(n_worst_segments_relative, args.export)
            else:
                if args.format is None:
                    print("Export format not specified. Use '-f json' or '-f csv'.")
                else:
                    print(
                        f"Unsupported export format: {args.format}. Use '-f json' or '-f csv'."
                    )
                return


if __name__ == "__main__":
    main()
