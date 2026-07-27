import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from chicago_traffic.models import TrafficSegment

CACHE_PATH = Path(".cache/historical_speeds.json")


def load_cached_historical(max_age: timedelta) -> list[TrafficSegment] | None:
    if not Path(CACHE_PATH).exists():
        return None

    try:
        with open(CACHE_PATH, "r") as f:
            cached_data = json.load(f)

        cached_timestamp = datetime.fromisoformat(cached_data["timestamp"])

        if datetime.now(UTC) - cached_timestamp > max_age:
            return None

        segments = [
            TrafficSegment(
                **{
                    **segment_dict,
                    "last_updated": datetime.fromisoformat(
                        segment_dict["last_updated"]
                    ),
                }
            )
            for segment_dict in cached_data["segments"]
        ]

        return segments
    except Exception:  # noqa: BLE001
        return None


def save_historical_cache(segments: list[TrafficSegment]) -> None:
    dict_to_cache = {
        "timestamp": datetime.now(UTC).isoformat(),
        "segments": [
            {
                **segment.__dict__,
                "last_updated": segment.last_updated.isoformat(),
            }
            for segment in segments
        ],
    }

    Path(".cache").mkdir(exist_ok=True)

    with open(CACHE_PATH, "w") as f:
        json.dump(dict_to_cache, f)
