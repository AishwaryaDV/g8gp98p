"""Core domain logic: pick the decision-time forecast and line it up with actuals.

Two things happen here, and both are the heart of the product:

1. Vintage selection (no look-ahead): for a delivery day D, a trader deciding on
   D-1 only knows forecasts published at/before the D-1 cut-off. We select, per
   target hour, the *latest* forecast published at or before that cut-off.

2. Resolution alignment: actuals are half-hourly, forecasts are hourly. The
   forecast carries no sub-hourly information, so rather than fabricate 30-min
   forecast detail we aggregate actuals up to the hourly grid (mean MW of the
   two settlement periods in the hour) and compare on that common grid.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import pandas as pd

from . import config, elexon


def decision_cutoff(delivery_day: date) -> datetime:
    """Information cut-off instant for a given delivery day (11:00 UTC on D-1)."""
    d_minus_1 = delivery_day - timedelta(days=1)
    return datetime.combine(
        d_minus_1, time(config.DECISION_CUTOFF_HOUR_UTC, 0), tzinfo=timezone.utc
    )


def decision_time_forecast(delivery_day: date) -> pd.DataFrame:
    """The hourly wind forecast a trader would have had for `delivery_day`.

    Returns columns: start_time, generation (MW). One row per target hour of the
    delivery day, taken from the latest vintage published at/before the cut-off.
    """
    fc = elexon.load_forecasts()
    cutoff = decision_cutoff(delivery_day)

    day_start = datetime.combine(delivery_day, time(0, 0), tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    mask = (
        (fc["start_time"] >= day_start)
        & (fc["start_time"] < day_end)
        & (fc["publish_time"] <= cutoff)
    )
    window = fc[mask]
    if window.empty:
        return pd.DataFrame(columns=["start_time", "generation"])

    # For each target hour keep the most recently published value.
    window = window.sort_values("publish_time")
    latest = window.groupby("start_time", as_index=False).last()
    return latest[["start_time", "generation"]].sort_values("start_time").reset_index(
        drop=True
    )


def actuals_hourly(day_start: datetime, day_end: datetime) -> pd.DataFrame:
    """Actual wind generation aggregated to the hourly grid (mean MW)."""
    act = elexon.load_actuals()
    mask = (act["start_time"] >= day_start) & (act["start_time"] < day_end)
    window = act[mask].copy()
    if window.empty:
        return pd.DataFrame(columns=["start_time", "generation"])
    window["hour"] = window["start_time"].dt.floor("h")
    hourly = window.groupby("hour", as_index=False)["generation"].mean()
    return hourly.rename(columns={"hour": "start_time"})


def aligned_day(delivery_day: date) -> pd.DataFrame:
    """Forecast vs actual for one delivery day on the common hourly grid.

    Columns: start_time, forecast, actual, error (forecast - actual).
    """
    day_start = datetime.combine(delivery_day, time(0, 0), tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    fc = decision_time_forecast(delivery_day).rename(
        columns={"generation": "forecast"}
    )
    act = actuals_hourly(day_start, day_end).rename(columns={"generation": "actual"})

    merged = pd.merge(fc, act, on="start_time", how="outer").sort_values("start_time")
    merged["error"] = merged["forecast"] - merged["actual"]
    return merged.reset_index(drop=True)


def aligned_range(start: date, end: date) -> pd.DataFrame:
    """Concatenate aligned day frames across an inclusive date range."""
    frames = []
    day = start
    while day <= end:
        frames.append(aligned_day(day))
        day += timedelta(days=1)
    if not frames:
        return pd.DataFrame(columns=["start_time", "forecast", "actual", "error"])
    return pd.concat(frames, ignore_index=True)


def available_days() -> list[date]:
    """Delivery days in the configured month that have both forecast and actual."""
    days = []
    day = config.MONTH_START
    while day <= config.MONTH_END:
        days.append(day)
        day += timedelta(days=1)
    return days
