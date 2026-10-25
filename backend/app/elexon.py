"""Thin client for the Elexon BMRS public datasets we depend on.

We fetch the whole January-2026 window once and cache the raw frames in memory.
The data is historical and immutable, so a single fetch per process is enough
and keeps the UI snappy (and resilient to Elexon latency during a demo).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd

from . import config

# Fetch a little before/after the month so we have every forecast vintage that
# a January delivery day could have used (earliest decision cut-off is
# 31 Dec 2025) and every actual published just after the month ends.
_FETCH_FROM = datetime(2025, 12, 30, 0, 0, tzinfo=timezone.utc)
_FETCH_TO = datetime(2026, 2, 1, 3, 0, tzinfo=timezone.utc)

_cache: dict[str, pd.DataFrame] = {}


def _get_stream(url: str) -> list[dict]:
    """Pull a BMRS stream endpoint for the configured publish-time window."""
    params = {
        "publishDateTimeFrom": _FETCH_FROM.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishDateTimeTo": _FETCH_TO.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def load_actuals() -> pd.DataFrame:
    """Actual national wind generation (FUELHH, fuelType=WIND), 30-min grid.

    Columns: start_time (tz-aware UTC), generation (MW).
    """
    if "actuals" not in _cache:
        rows = _get_stream(config.FUELHH_STREAM)
        df = pd.DataFrame(rows)
        df = df[df["fuelType"] == "WIND"].copy()
        df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
        df = df[["start_time", "generation"]].sort_values("start_time")
        df = df.drop_duplicates(subset="start_time", keep="last").reset_index(drop=True)
        _cache["actuals"] = df
    return _cache["actuals"]


def load_forecasts() -> pd.DataFrame:
    """All wind forecast vintages (WINDFOR), hourly target grid.

    Columns: publish_time, start_time (both tz-aware UTC), generation (MW).
    We keep every vintage; vintage selection happens in `alignment`.
    """
    if "forecasts" not in _cache:
        rows = _get_stream(config.WINDFOR_STREAM)
        df = pd.DataFrame(rows)
        df["publish_time"] = pd.to_datetime(df["publishTime"], utc=True)
        df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
        df = df[["publish_time", "start_time", "generation"]].sort_values(
            ["start_time", "publish_time"]
        )
        _cache["forecasts"] = df.reset_index(drop=True)
    return _cache["forecasts"]


def warm_cache() -> None:
    """Prefetch both datasets (called on startup)."""
    load_actuals()
    load_forecasts()
