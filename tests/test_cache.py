from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from worst_commute_finder.cache import load_cached_historical, save_historical_cache


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    pass


def test_save_then_load_round_trip(isolated_cache):
    """Segments saved via save_historical_cache should come back identical (including
    last_updated as a real datetime, not a string) via load_cached_historical."""
    pass


def test_load_returns_none_when_file_missing(isolated_cache):
    """No cache file at all -> returns None, no exception."""
    pass


def test_load_returns_none_when_stale(isolated_cache, monkeypatch):
    """Cache older than max_age returns None (treated as a miss)."""
    # TODO: write a cache with an old timestamp, then call load_cached_historical
    # with a max_age smaller than the elapsed time
    pass


def test_load_returns_segments_when_fresh(isolated_cache):
    """Cache within max_age returns the segments, not None."""
    pass


def test_load_returns_none_on_corrupted_json(isolated_cache):
    """Malformed/corrupted cache file is treated as a miss, not an unhandled exception."""
    pass


def test_load_returns_none_on_missing_keys(isolated_cache):
    """Cache file missing expected keys (e.g. 'segments' or 'timestamp') is treated as a miss."""
    pass


def test_save_creates_cache_directory_if_missing(tmp_path, monkeypatch):
    """.cache/ directory is created if it doesn't already exist."""
    pass
