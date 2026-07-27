from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from chicago_traffic.models import TrafficSegment

from tests.test_ranker import make_segment
from worst_commute_finder.cache import load_cached_historical, save_historical_cache


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    """Point cache.CACHE_PATH at a tmp_path location so tests don't touch the real .cache/."""
    cache_file = tmp_path / "historical_speeds.json"
    monkeypatch.setattr("worst_commute_finder.cache.CACHE_PATH", cache_file)
    return cache_file


def test_save_then_load_round_trip(isolated_cache):
    """Segments saved via save_historical_cache should come back identical (including
    last_updated as a real datetime, not a string) via load_cached_historical."""
    segments_to_save: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=20.0, last_updated=datetime.now(UTC)),
        make_segment(
            segment_id=2,
            current_speed=30.0,
            last_updated=datetime.now(UTC) - timedelta(minutes=5),
        ),
    ]

    save_historical_cache(segments_to_save)

    loaded_segments: list[TrafficSegment] | None = load_cached_historical(
        max_age=timedelta(days=1)
    )

    assert isolated_cache.exists()
    assert loaded_segments is not None
    assert len(loaded_segments) == len(segments_to_save)

    for saved, loaded in zip(segments_to_save, loaded_segments):
        assert saved.segment_id == loaded.segment_id
        assert saved.current_speed == loaded.current_speed
        assert isinstance(loaded.last_updated, datetime)
        assert loaded.last_updated.tzinfo is not None


def test_load_returns_none_when_file_missing(isolated_cache):
    """No cache file at all -> returns None, no exception."""
    assert not isolated_cache.exists()

    loaded_segments: list[TrafficSegment] | None = load_cached_historical(
        max_age=timedelta(days=1)
    )

    assert loaded_segments is None


def test_load_returns_none_when_stale(isolated_cache, monkeypatch):
    """Cache older than max_age returns None (treated as a miss)."""
    # TODO: write a cache with an old timestamp, then call load_cached_historical
    # with a max_age smaller than the elapsed time
    old_cache_segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1,
            current_speed=20.0,
            last_updated=datetime.now(UTC) - timedelta(days=2),
        ),
    ]

    save_historical_cache(old_cache_segments)

    assert isolated_cache.exists()

    loaded_segments: list[TrafficSegment] | None = load_cached_historical(
        max_age=timedelta(days=1)
    )

    assert loaded_segments is None


def test_load_returns_segments_when_fresh(isolated_cache):
    """Cache within max_age returns the segments, not None."""
    fresh_cache_segments: list[TrafficSegment] = [
        make_segment(
            segment_id=1,
            current_speed=20.0,
            last_updated=datetime.now(UTC) - timedelta(minutes=5),
        ),
    ]

    save_historical_cache(fresh_cache_segments)

    assert isolated_cache.exists()

    loaded_segments: list[TrafficSegment] | None = load_cached_historical(
        max_age=timedelta(days=1)
    )

    assert loaded_segments is not None
    assert len(loaded_segments) == len(fresh_cache_segments)
    assert loaded_segments[0].segment_id == fresh_cache_segments[0].segment_id
    assert loaded_segments[0].current_speed == fresh_cache_segments[0].current_speed


def test_load_returns_none_on_corrupted_json(isolated_cache):
    """Malformed/corrupted cache file is treated as a miss, not an unhandled exception."""
    # Write a corrupted JSON file
    with open(isolated_cache, "w") as f:
        f.write("{ this is not valid JSON }")

    loaded_segments: list[TrafficSegment] | None = load_cached_historical(
        max_age=timedelta(days=1)
    )

    assert loaded_segments is None


def test_load_returns_none_on_missing_keys(isolated_cache):
    """Cache file missing expected keys (e.g. 'segments' or 'timestamp') is treated as a miss."""
    # Write a JSON file missing the 'segments' key
    with open(isolated_cache, "w") as f:
        f.write('{"timestamp": "2024-01-01T00:00:00Z"}')

    loaded_segments: list[TrafficSegment] | None = load_cached_historical(
        max_age=timedelta(days=1)
    )

    assert loaded_segments is None


def test_save_creates_cache_directory_if_missing(tmp_path, monkeypatch):
    """.cache/ directory is created if it doesn't already exist."""
    cache_file = tmp_path / "historical_speeds.json"
    monkeypatch.setattr("worst_commute_finder.cache.CACHE_PATH", cache_file)

    # Ensure the .cache directory does not exist
    cache_dir = cache_file.parent
    assert not cache_dir.exists()

    segments_to_save: list[TrafficSegment] = [
        make_segment(segment_id=1, current_speed=20.0, last_updated=datetime.now(UTC)),
    ]

    save_historical_cache(segments_to_save)

    # After saving, the .cache directory should exist
    assert cache_dir.exists()
